#!/usr/bin/env python3
"""Sync all collections from Atlas to local MongoDB - removes _id to avoid duplicates"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne
import os, time, sys
from dotenv import load_dotenv
load_dotenv()

BATCH_SIZE = 5000
LOG_FILE = "/tmp/sync_progress.log"

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

async def sync_collection(cloud_db, local_db, col_name):
    start = time.time()
    total = await cloud_db[col_name].count_documents({})
    local_count = await local_db[col_name].count_documents({})
    
    if local_count >= total:
        log(f"{col_name}: SKIP (local {local_count:,} >= cloud {total:,})")
        return
    
    log(f"{col_name}: START - dropping local and syncing {total:,} docs")
    
    # Drop entire collection for clean start
    await local_db[col_name].drop()
    
    synced = 0
    batch = []
    cursor = cloud_db[col_name].find({}).batch_size(BATCH_SIZE)
    
    async for doc in cursor:
        doc.pop('_id', None)  # Remove _id to avoid duplicate key errors
        batch.append(InsertOne(doc))
        if len(batch) >= BATCH_SIZE:
            await local_db[col_name].bulk_write(batch, ordered=False)
            synced += len(batch)
            batch = []
            elapsed = time.time() - start
            speed = synced / elapsed if elapsed > 0 else 0
            pct = int(synced / total * 100)
            if synced % 50000 == 0:
                log(f"  {col_name}: {synced:,}/{total:,} ({pct}%) - {speed:,.0f} docs/s")
    
    if batch:
        await local_db[col_name].bulk_write(batch, ordered=False)
        synced += len(batch)
    
    elapsed = time.time() - start
    speed = synced / elapsed if elapsed > 0 else 0
    log(f"{col_name}: DONE {synced:,} docs in {elapsed:.1f}s ({speed:,.0f} docs/s)")

async def main():
    cloud_url = os.environ.get('CLOUD_MONGO_URL', '')
    cloud_client = AsyncIOMotorClient(cloud_url)
    local_client = AsyncIOMotorClient('mongodb://localhost:27017/')
    
    cloud_db = cloud_client['justportal']
    local_db = local_client['mfirme_local']
    
    with open(LOG_FILE, "w") as f:
        f.write("")
    
    log("=== START SYNC COMPLET DIN ATLAS ===")
    
    if len(sys.argv) > 1:
        collections = [sys.argv[1]]
    else:
        collections = ['lichidatori', 'bpi_records', 'bilanturi', 'dosare', 'firme']
    
    for col in collections:
        await sync_collection(cloud_db, local_db, col)
    
    log("=== VERIFICARE FINALA ===")
    for col in ['lichidatori', 'bpi_records', 'bilanturi', 'dosare', 'firme']:
        count = await local_db[col].count_documents({})
        log(f"  {col}: {count:,}")
    
    cloud_client.close()
    local_client.close()
    log("SYNC COMPLET!")

asyncio.run(main())
