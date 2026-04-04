"""
Admin Sync Routes
Endpoints pentru controlul sincronizării MongoDB local/cloud
Sync direct în backend (fără sync-service separat)
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import re
import os
from datetime import datetime, timezone
from auth import get_current_user
from database import get_app_db, get_local_db, get_cloud_db, check_local_db_health
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne
from pymongo.errors import BulkWriteError
import logging
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/sync", tags=["admin-sync"])

# Sync state (in-memory for this instance)
sync_state = {
    "is_running": False,
    "current_collection": None,
    "progress": 0,
    "total": 0,
    "synced": 0,
    "status": "idle",
    "last_sync": None,
    "errors": [],
    "collections_status": {},
    "logs": []
}

MAX_LOGS = 100

def add_sync_log(message, level="info"):
    """Add a log entry to sync state"""
    sync_state["logs"].append({
        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "message": message,
        "level": level
    })
    if len(sync_state["logs"]) > MAX_LOGS:
        sync_state["logs"] = sync_state["logs"][-MAX_LOGS:]

BATCH_SIZE = 5000


class SyncRequest(BaseModel):
    cloud_url: Optional[str] = None


async def verify_admin(current_user = Depends(get_current_user)):
    """Verify user is admin"""
    app_db = get_app_db()
    user = await app_db.users.find_one({"email": current_user["email"]})
    
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user


async def sync_collection(cloud_db, local_db, collection_name: str) -> Dict[str, Any]:
    """Sync a single collection from cloud to local"""
    global sync_state
    
    start_time = datetime.now(timezone.utc)
    sync_state["current_collection"] = collection_name
    sync_state["status"] = f"syncing_{collection_name}"
    
    try:
        # Get total count
        total_count = await cloud_db[collection_name].count_documents({})
        sync_state["total"] = total_count
        sync_state["synced"] = 0
        sync_state["progress"] = 0
        
        add_sync_log(f"Start sync {collection_name}: {total_count:,} documente")
        
        # Clear local collection
        await local_db[collection_name].delete_many({})
        add_sync_log(f"{collection_name}: colecția locală curățată")
        
        # Sync in batches
        synced = 0
        skipped = 0
        cursor = cloud_db[collection_name].find({}).batch_size(BATCH_SIZE)
        
        batch = []
        async for doc in cursor:
            doc.pop('_id', None)
            batch.append(InsertOne(doc))
            
            if len(batch) >= BATCH_SIZE:
                try:
                    result = await local_db[collection_name].bulk_write(batch, ordered=False)
                    synced += result.inserted_count
                except BulkWriteError as bwe:
                    synced += bwe.details.get('nInserted', 0)
                    skipped += len(bwe.details.get('writeErrors', []))
                sync_state["synced"] = synced
                sync_state["progress"] = int((synced / total_count) * 100) if total_count > 0 else 100
                
                add_sync_log(f"{collection_name}: {synced:,}/{total_count:,} ({sync_state['progress']}%) | skip: {skipped:,}")
                batch = []
        
        # Insert remaining
        if batch:
            try:
                result = await local_db[collection_name].bulk_write(batch, ordered=False)
                synced += result.inserted_count
            except BulkWriteError as bwe:
                synced += bwe.details.get('nInserted', 0)
                skipped += len(bwe.details.get('writeErrors', []))
            sync_state["synced"] = synced
        
        # Create indexes
        await create_indexes(local_db, collection_name)
        add_sync_log(f"{collection_name}: indexuri create")
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Update collection status
        sync_state["collections_status"][collection_name] = {
            "status": "synced",
            "documents": synced,
            "last_sync": end_time.isoformat(),
            "duration_seconds": duration
        }
        
        # Save sync status to local DB
        await local_db.sync_status.update_one(
            {"collection": collection_name},
            {"$set": {
                "status": "synced",
                "documents_count": synced,
                "last_full_sync": end_time,
                "duration_seconds": duration
            }},
            upsert=True
        )
        
        add_sync_log(f"✓ {collection_name} complet: {synced:,} docs în {duration:.0f}s", "success")
        
        return {
            "collection": collection_name,
            "documents": synced,
            "duration_seconds": duration,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error syncing {collection_name}: {e}")
        add_sync_log(f"✗ Eroare {collection_name}: {str(e)}", "error")
        sync_state["errors"].append({
            "collection": collection_name,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        sync_state["collections_status"][collection_name] = {
            "status": "error",
            "error": str(e)
        }
        return {
            "collection": collection_name,
            "status": "error",
            "error": str(e)
        }


async def create_indexes(local_db, collection_name: str):
    """Create indexes for collection"""
    try:
        if collection_name == 'firme':
            await local_db[collection_name].create_index('cui', unique=True)
            await local_db[collection_name].create_index('denumire')
            await local_db[collection_name].create_index('id')
            await local_db[collection_name].create_index('judet')
            await local_db[collection_name].create_index('localitate')
            await local_db[collection_name].create_index('anaf_cod_caen')
            await local_db[collection_name].create_index('has_dosare')
            await local_db[collection_name].create_index([('judet', 1), ('localitate', 1)])
            await local_db[collection_name].create_index([('denumire', 'text')])
            logger.info(f"  Created indexes for {collection_name}")
            
        elif collection_name == 'bilanturi':
            await local_db[collection_name].create_index('firma_id')
            await local_db[collection_name].create_index('an')
            await local_db[collection_name].create_index([('firma_id', 1), ('an', -1)])
            logger.info(f"  Created indexes for {collection_name}")
            
        elif collection_name == 'caen_codes':
            await local_db[collection_name].create_index('cod', unique=True)
            logger.info(f"  Created indexes for {collection_name}")
        
        elif collection_name == 'dosare':
            await local_db[collection_name].create_index('firma_id')
            await local_db[collection_name].create_index('numar_dosar')
            await local_db[collection_name].create_index('institutie')
            await local_db[collection_name].create_index('data_dosar')
            await local_db[collection_name].create_index([('firma_id', 1), ('data_dosar', -1)])
            logger.info(f"  Created indexes for {collection_name}")
        
        elif collection_name == 'bpi_records':
            await local_db[collection_name].create_index('cui')
            await local_db[collection_name].create_index('dosar')
            await local_db[collection_name].create_index('tip_procedura')
            await local_db[collection_name].create_index('data_publicare')
            await local_db[collection_name].create_index([('denumire_firma', 'text')])
            logger.info(f"  Created indexes for {collection_name}")
        
        elif collection_name == 'lichidatori':
            await local_db[collection_name].create_index('nume')
            await local_db[collection_name].create_index('nume_normalized')
            await local_db[collection_name].create_index('cui')
            await local_db[collection_name].create_index('firme.cui')
            logger.info(f"  Created indexes for {collection_name}")
            
    except Exception as e:
        logger.warning(f"Error creating indexes for {collection_name}: {e}")


async def run_full_sync(cloud_db, local_db, collections: list):
    """Run full sync for all collections"""
    global sync_state
    
    sync_state["is_running"] = True
    sync_state["status"] = "running"
    sync_state["errors"] = []
    sync_state["logs"] = []
    
    add_sync_log(f"Sync pornit pentru: {', '.join(collections)}")
    
    results = {}
    
    for collection in collections:
        if not sync_state["is_running"]:
            add_sync_log("Sync oprit de utilizator", "warning")
            break
        results[collection] = await sync_collection(cloud_db, local_db, collection)
    
    sync_state["is_running"] = False
    sync_state["status"] = "completed"
    sync_state["current_collection"] = None
    sync_state["last_sync"] = datetime.now(timezone.utc).isoformat()
    
    add_sync_log("Sincronizare completă!", "success")
    
    return results


@router.get("/status")
async def get_sync_status(admin_user = Depends(verify_admin)):
    """Get comprehensive sync status"""
    import time
    
    local_health = await check_local_db_health()
    
    # Measure local DB latency
    local_latency = None
    local_db = get_local_db()
    if local_db is not None:
        try:
            start = time.perf_counter()
            await local_db.command('ping')
            local_latency = round((time.perf_counter() - start) * 1000, 2)  # ms
        except:
            pass
    
    # Measure query speed (count query)
    query_speed = None
    if local_db is not None:
        try:
            start = time.perf_counter()
            await local_db.firme.find_one({})
            query_speed = round((time.perf_counter() - start) * 1000, 2)  # ms
        except:
            pass
    
    cloud_db = get_cloud_db()
    cloud_counts = {}
    cloud_connected = False
    cloud_latency = None
    
    if cloud_db is not None:
        try:
            # Measure cloud latency
            start = time.perf_counter()
            await cloud_db.command('ping')
            cloud_latency = round((time.perf_counter() - start) * 1000, 2)  # ms
            
            # Get counts for ALL collections
            for col in ['firme', 'bilanturi', 'dosare', 'bpi_records', 'lichidatori']:
                try:
                    cloud_counts[col] = await cloud_db[col].estimated_document_count()
                except:
                    cloud_counts[col] = 0
            cloud_connected = True
        except Exception as e:
            cloud_counts["error"] = str(e)
    
    return {
        "mode": "local",
        "local_db": local_health,
        "local_performance": {
            "ping_ms": local_latency,
            "query_ms": query_speed,
            "status": "fast" if local_latency and local_latency < 5 else "normal" if local_latency else "unknown"
        },
        "cloud_counts": cloud_counts,
        "cloud_connected": cloud_connected,
        "cloud_latency_ms": cloud_latency,
        "sync_state": {
            "is_running": sync_state["is_running"],
            "status": sync_state["status"],
            "current_collection": sync_state["current_collection"],
            "progress": sync_state["progress"],
            "synced": sync_state["synced"],
            "total": sync_state["total"],
            "last_sync": sync_state["last_sync"],
            "collections_status": sync_state["collections_status"],
            "errors": sync_state["errors"][-5:],
            "logs": sync_state["logs"][-30:]
        }
    }


@router.post("/direct-sync")
async def trigger_direct_sync(
    background_tasks: BackgroundTasks,
    collection: Optional[str] = None,
    admin_user = Depends(verify_admin)
):
    """
    Trigger direct sync from cloud to local (no sync-service needed)
    - If collection is specified, sync only that collection
    - Otherwise sync all: firme, bilanturi
    """
    global sync_state
    
    logger.info("=== DIRECT SYNC REQUEST ===")
    logger.info(f"Collection param: {collection}")
    logger.info(f"Admin user: {admin_user.get('email', 'unknown')}")
    
    if sync_state["is_running"]:
        logger.warning("Sync already in progress")
        raise HTTPException(status_code=409, detail="Sync already in progress")
    
    cloud_db = get_cloud_db()
    local_db = get_local_db()
    
    logger.info(f"Cloud DB available: {cloud_db is not None}")
    logger.info(f"Local DB available: {local_db is not None}")
    
    # Check environment variable
    import os
    cloud_url = os.getenv("CLOUD_MONGO_URL")
    logger.info(f"CLOUD_MONGO_URL set: {bool(cloud_url)}")
    if cloud_url:
        # Log only first 30 chars for security
        logger.info(f"CLOUD_MONGO_URL starts with: {cloud_url[:30]}...")
    
    if cloud_db is None:
        error_msg = "Cloud database not connected. Add CLOUD_MONGO_URL to backend/.env file"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    
    if local_db is None:
        error_msg = "Local database not connected. Check MONGO_URL in backend/.env"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Define collections to sync
    # UPDATED: Include all new collections (dosare, bpi_records, lichidatori)
    ALLOWED_COLLECTIONS = ['firme', 'bilanturi', 'caen_codes', 'dosare', 'bpi_records', 'lichidatori']
    
    if collection:
        if collection not in ALLOWED_COLLECTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid collection. Allowed: {ALLOWED_COLLECTIONS}")
        collections = [collection]
    else:
        # Default: sync all main collections
        collections = ['firme', 'bilanturi', 'dosare', 'bpi_records', 'lichidatori']
    
    # Start sync in background
    background_tasks.add_task(run_full_sync, cloud_db, local_db, collections)
    
    return {
        "status": "started",
        "message": f"Sync started for: {', '.join(collections)}",
        "collections": collections,
        "tip": "Check /api/admin/sync/status for progress"
    }


@router.post("/stop-sync")
async def stop_sync(admin_user = Depends(verify_admin)):
    """Stop ongoing sync"""
    global sync_state
    
    if not sync_state["is_running"]:
        return {"status": "not_running", "message": "No sync in progress"}
    
    sync_state["is_running"] = False
    sync_state["status"] = "stopping"
    
    return {"status": "stopping", "message": "Sync will stop after current batch"}


class CloudUrlRequest(BaseModel):
    cloud_url: str


@router.post("/set-cloud-url")
async def set_cloud_url(request: CloudUrlRequest, admin_user = Depends(verify_admin)):
    """Set cloud MongoDB URL at runtime (without restart)"""
    import database
    
    cloud_url = request.cloud_url.strip()
    if not cloud_url:
        raise HTTPException(status_code=400, detail="Cloud URL is required")
    
    try:
        # Close existing cloud connection
        if database.cloud_companies_client:
            database.cloud_companies_client.close()
        
        # Connect with new URL
        client = AsyncIOMotorClient(cloud_url, serverSelectionTimeoutMS=10000)
        db = client["justportal"]
        await db.command('ping')
        
        # Update global references
        database.cloud_companies_client = client
        database.cloud_companies_db = db
        
        # Get collection counts
        counts = {}
        for col in ['firme', 'bilanturi', 'dosare', 'bpi_records', 'lichidatori']:
            try:
                counts[col] = await db[col].estimated_document_count()
            except:
                counts[col] = 0
        
        logger.info(f"Cloud MongoDB connected successfully via admin UI")
        
        return {
            "status": "connected",
            "message": "Cloud MongoDB conectat cu succes",
            "collections": counts
        }
    except Exception as e:
        logger.error(f"Failed to connect to cloud MongoDB: {e}")
        raise HTTPException(status_code=400, detail=f"Nu s-a putut conecta: {str(e)}")


@router.post("/create-indexes")
async def create_all_indexes(admin_user = Depends(verify_admin)):
    """Create indexes on all collections (without re-sync)"""
    local_db = get_local_db()
    if local_db is None:
        raise HTTPException(status_code=400, detail="Local DB not connected")
    
    collections = ['firme', 'bilanturi', 'dosare', 'bpi_records', 'caen_codes']
    results = {}
    for col in collections:
        try:
            count = await local_db[col].estimated_document_count()
            if count > 0:
                await create_indexes(local_db, col)
                results[col] = f"Indexes created ({count:,} docs)"
            else:
                results[col] = "Skipped (empty)"
        except Exception as e:
            results[col] = f"Error: {str(e)}"
    
    return {"status": "ok", "results": results}


@router.get("/health")
async def check_connections(admin_user = Depends(verify_admin)):
    """Check database connections"""
    results = {}
    
    # Check local
    local_db = get_local_db()
    if local_db is not None:
        try:
            await local_db.command('ping')
            results["local"] = {"status": "connected"}
        except Exception as e:
            results["local"] = {"status": "error", "error": str(e)}
    else:
        results["local"] = {"status": "not_configured"}
    
    # Check cloud
    cloud_db = get_cloud_db()
    if cloud_db is not None:
        try:
            await cloud_db.command('ping')
            results["cloud"] = {"status": "connected"}
        except Exception as e:
            results["cloud"] = {"status": "error", "error": str(e)}
    else:
        results["cloud"] = {"status": "not_configured"}
    
    return results


@router.get("/local-stats")
async def get_local_db_stats(admin_user = Depends(verify_admin)):
    """Get detailed statistics about local database"""
    local_db = get_local_db()
    
    if local_db is None:
        return {"available": False, "message": "Local DB not configured"}
    
    try:
        stats = {}
        collections = ['firme', 'bilanturi', 'dosare', 'bpi_records', 'lichidatori', 'caen_codes', 'postal_codes', 'localities', 'sync_status']
        
        for col in collections:
            try:
                count = await local_db[col].count_documents({})
                stats[col] = {"count": count}
            except Exception as e:
                stats[col] = {"error": str(e)}
        
        return {
            "database": "mfirme_local",
            "collections": stats,
            "total_documents": sum(s.get("count", 0) for s in stats.values() if isinstance(s.get("count"), int))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Keep old endpoints for backwards compatibility
@router.post("/trigger-full")
async def trigger_full_sync_legacy(
    background_tasks: BackgroundTasks,
    request: Request,
    admin_user = Depends(verify_admin)
):
    """Legacy endpoint - redirects to direct-sync"""
    return await trigger_direct_sync(background_tasks, None, admin_user)


@router.post("/trigger-collection/{collection_name}")
async def trigger_collection_sync_legacy(
    collection_name: str,
    background_tasks: BackgroundTasks,
    admin_user = Depends(verify_admin)
):
    """Legacy endpoint - redirects to direct-sync"""
    return await trigger_direct_sync(background_tasks, collection_name, admin_user)


# ============================================================
# Import Reference Data (CAEN codes, postal codes, localities)
# These are NOT in cloud Atlas - imported from external sources
# ============================================================

import_state = {
    "is_running": False,
    "status": "idle",
    "progress": "",
    "error": None
}


@router.get("/import-status")
async def get_import_status(admin_user = Depends(verify_admin)):
    """Get status of reference data import"""
    return import_state


@router.post("/import-reference-data")
async def import_reference_data(
    background_tasks: BackgroundTasks,
    admin_user = Depends(verify_admin)
):
    """Import CAEN codes, postal codes and localities into local DB"""
    global import_state
    
    if import_state["is_running"]:
        raise HTTPException(status_code=409, detail="Import already running")
    
    local_db = get_local_db()
    if local_db is None:
        raise HTTPException(status_code=400, detail="Local DB not connected")
    
    import_state["is_running"] = True
    import_state["status"] = "starting"
    import_state["error"] = None
    
    background_tasks.add_task(run_reference_import, local_db)
    
    return {"status": "started", "message": "Import date de referință pornit"}


async def run_reference_import(local_db):
    """Background task to import all reference data"""
    global import_state
    
    try:
        # 1. Import CAEN codes
        import_state["status"] = "importing"
        import_state["progress"] = "Import coduri CAEN..."
        await import_caen_codes(local_db)
        
        # 2. Import postal codes + localities
        import_state["progress"] = "Download și import coduri poștale..."
        await import_postal_codes(local_db)
        
        import_state["status"] = "completed"
        import_state["progress"] = "Import complet!"
        logger.info("Reference data import completed successfully")
        
    except Exception as e:
        import_state["status"] = "error"
        import_state["error"] = str(e)
        logger.error(f"Reference data import error: {e}")
    finally:
        import_state["is_running"] = False


async def import_caen_codes(local_db):
    """Import CAEN Rev.2 codes from embedded data"""
    from scripts.import_caen_codes import CAEN_REV2_CODES
    
    await local_db.caen_codes.drop()
    
    docs = []
    for code, description in CAEN_REV2_CODES:
        section = code[0:2]
        docs.append({
            "cod": code,
            "name": description,
            "description": description,
            "section": section
        })
    
    if docs:
        await local_db.caen_codes.insert_many(docs)
        await local_db.caen_codes.create_index("cod", unique=True)
    
    import_state["progress"] = f"CAEN: {len(docs)} coduri importate"
    logger.info(f"Imported {len(docs)} CAEN codes")


async def import_postal_codes(local_db):
    """Import postal codes from GitHub SQL file and create localities"""
    
    INSERT_PATTERN = re.compile(
        r"\((\d+),\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\)"
    )
    
    DIACRITICS = {
        'ş': 's', 'Ş': 'S', 'ș': 's', 'Ș': 'S',
        'ţ': 't', 'Ţ': 'T', 'ț': 't', 'Ț': 'T',
        'ă': 'a', 'Ă': 'A', 'â': 'a', 'Â': 'A',
        'î': 'i', 'Î': 'I'
    }
    
    def normalize(text):
        result = re.sub(r'\([^)]*\)', '', text).strip()
        for old, new in DIACRITICS.items():
            result = result.replace(old, new)
        return result.upper()
    
    # Download SQL file
    sql_url = "https://raw.githubusercontent.com/romania/localitati/refs/heads/master/coduri_postale.sql"
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(sql_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download postal codes: HTTP {response.status_code}")
        sql_content = response.text
    
    # Parse SQL
    records = []
    for match in INSERT_PATTERN.finditer(sql_content):
        record = {
            'id': int(match.group(1)),
            'judet': match.group(2).strip(),
            'localitate': match.group(3).strip(),
            'tip_artera': match.group(4).strip() or None,
            'denumire_artera': match.group(5).strip() or None,
            'numar_bloc': match.group(6).strip() or None,
            'cod_postal': match.group(7).strip(),
            'judet_normalized': normalize(match.group(2).strip()),
            'localitate_normalized': normalize(match.group(3).strip())
        }
        records.append(record)
    
    if not records:
        raise Exception("No postal codes found in SQL file")
    
    import_state["progress"] = f"Coduri poștale: {len(records)} parsed, inserting..."
    
    # Insert postal codes
    await local_db.postal_codes.drop()
    batch_size = 5000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        await local_db.postal_codes.insert_many(batch)
    
    await local_db.postal_codes.create_index("cod_postal")
    await local_db.postal_codes.create_index("judet")
    await local_db.postal_codes.create_index("judet_normalized")
    await local_db.postal_codes.create_index("localitate_normalized")
    await local_db.postal_codes.create_index([("judet_normalized", 1), ("localitate_normalized", 1)])
    
    import_state["progress"] = f"Coduri poștale: {len(records)} importate. Generez localități..."
    logger.info(f"Imported {len(records)} postal codes")
    
    # Create localities (aggregated from postal codes)
    pipeline = [
        {"$group": {
            "_id": {
                "judet": "$judet",
                "judet_normalized": "$judet_normalized",
                "localitate": "$localitate",
                "localitate_normalized": "$localitate_normalized"
            },
            "postal_codes": {"$addToSet": "$cod_postal"},
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "judet": "$_id.judet",
            "judet_normalized": "$_id.judet_normalized",
            "localitate": "$_id.localitate",
            "localitate_normalized": "$_id.localitate_normalized",
            "postal_codes": 1,
            "postal_code_count": "$count",
            "primary_postal_code": {"$arrayElemAt": ["$postal_codes", 0]}
        }}
    ]
    
    await local_db.localities.drop()
    localities = await local_db.postal_codes.aggregate(pipeline).to_list(length=None)
    
    if localities:
        await local_db.localities.insert_many(localities)
        await local_db.localities.create_index([("judet_normalized", 1), ("localitate_normalized", 1)])
        await local_db.localities.create_index("localitate_normalized")
        await local_db.localities.create_index("judet")
    
    import_state["progress"] = f"Complet: {len(records)} coduri poștale, {len(localities)} localități, CAEN ok"
    logger.info(f"Created {len(localities)} localities")
