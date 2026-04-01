#!/usr/bin/env python3
"""
Pre-compute legal flags on firme collection using bulk operations.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
import time, os
from dotenv import load_dotenv
load_dotenv()

LOG_FILE = "/tmp/legal_flags_progress.log"

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client['mfirme_local']

    with open(LOG_FILE, "w") as f:
        f.write("")

    log("=== START: Pre-compute legal flags (BULK) ===")

    # Step 1: Aggregate dosare count per firma_id
    log("Step 1: Aggregating dosare per firma_id...")
    start = time.time()
    dosare_map = {}
    async for doc in db.dosare.aggregate([{"$group": {"_id": "$firma_id", "count": {"$sum": 1}}}]):
        if doc["_id"] is not None:
            dosare_map[doc["_id"]] = doc["count"]
    log(f"  {len(dosare_map):,} firme cu dosare ({time.time()-start:.1f}s)")

    # Step 2: Aggregate bpi count per CUI
    log("Step 2: Aggregating BPI per CUI...")
    start = time.time()
    bpi_map = {}
    async for doc in db.bpi_records.aggregate([{"$group": {"_id": "$cui", "count": {"$sum": 1}}}]):
        if doc["_id"] is not None:
            bpi_map[str(doc["_id"])] = doc["count"]
    log(f"  {len(bpi_map):,} firme cu BPI ({time.time()-start:.1f}s)")

    # Step 3: Reset all flags
    log("Step 3: Reset all legal flags...")
    start = time.time()
    await db.firme.update_many({}, {"$set": {
        "has_dosare": False, "dosare_count": 0,
        "has_bpi": False, "bpi_count": 0,
        "has_legal_issues": False
    }})
    log(f"  Reset done ({time.time()-start:.1f}s)")

    # Step 4: Bulk update firme with dosare
    log("Step 4: Bulk update dosare flags...")
    start = time.time()
    BATCH = 5000
    ops = []
    total_updated = 0
    
    for fid, count in dosare_map.items():
        ops.append(UpdateOne(
            {"id": fid},
            {"$set": {"has_dosare": True, "dosare_count": count, "has_legal_issues": True}}
        ))
        if len(ops) >= BATCH:
            await db.firme.bulk_write(ops, ordered=False)
            total_updated += len(ops)
            ops = []
            if total_updated % 50000 == 0:
                log(f"  Dosare: {total_updated:,}/{len(dosare_map):,}")
    
    if ops:
        await db.firme.bulk_write(ops, ordered=False)
        total_updated += len(ops)
    log(f"  {total_updated:,} firme updated with dosare ({time.time()-start:.1f}s)")

    # Step 5: Bulk update firme with BPI
    log("Step 5: Bulk update BPI flags...")
    start = time.time()
    ops = []
    total_updated = 0
    
    for cui, count in bpi_map.items():
        ops.append(UpdateOne(
            {"cui": cui},
            {"$set": {"has_bpi": True, "bpi_count": count, "has_legal_issues": True}}
        ))
        if len(ops) >= BATCH:
            await db.firme.bulk_write(ops, ordered=False)
            total_updated += len(ops)
            ops = []
    
    if ops:
        await db.firme.bulk_write(ops, ordered=False)
        total_updated += len(ops)
    log(f"  {total_updated:,} firme updated with BPI ({time.time()-start:.1f}s)")

    # Verify
    log("=== VERIFICARE ===")
    log(f"  Firme cu dosare: {await db.firme.count_documents({'has_dosare': True}):,}")
    log(f"  Firme cu BPI: {await db.firme.count_documents({'has_bpi': True}):,}")
    log(f"  Firme cu probleme juridice: {await db.firme.count_documents({'has_legal_issues': True}):,}")
    log("DONE!")

    client.close()

asyncio.run(main())
