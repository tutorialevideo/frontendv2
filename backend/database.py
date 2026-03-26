from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

logger = logging.getLogger(__name__)

# Cloud databases (MongoDB Atlas)
cloud_companies_client = None
cloud_companies_db = None

# App database (read-write for users, subscriptions, etc.)
app_client = None
app_db = None

# Local database (MongoDB Local - for fast reads)
local_client = None
local_db = None

# Configuration
USE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "false").lower() == "true"
LOCAL_DB_AVAILABLE = False

# Backwards compatibility aliases
companies_client = None
companies_db = None


async def connect_to_databases():
    global cloud_companies_client, cloud_companies_db
    global app_client, app_db
    global local_client, local_db
    global LOCAL_DB_AVAILABLE
    global companies_client, companies_db
    
    # Connect to cloud companies database (read-only source for firme)
    cloud_mongo_url = os.getenv("CLOUD_MONGO_URL")
    if cloud_mongo_url:
        try:
            cloud_companies_client = AsyncIOMotorClient(cloud_mongo_url)
            cloud_companies_db = cloud_companies_client["justportal"]
            await cloud_companies_db.command('ping')
            print("✓ Connected to MongoDB Cloud (justportal - firme source)")
        except Exception as e:
            print(f"✗ Failed to connect to cloud companies DB: {e}")
    
    # Connect to app database (users, settings, etc.)
    app_mongo_url = os.getenv("APP_MONGO_URL")
    if app_mongo_url:
        try:
            app_client = AsyncIOMotorClient(app_mongo_url)
            app_db = app_client["mfirme_app"]
            await app_db.command('ping')
            print("✓ Connected to MongoDB App (mfirme_app)")
        except Exception as e:
            print(f"✗ Failed to connect to app DB: {e}")
    
    # Connect to local MongoDB (for fast reads)
    local_mongo_url = os.getenv("MONGO_LOCAL_URL")
    if USE_LOCAL_DB and local_mongo_url:
        try:
            local_client = AsyncIOMotorClient(local_mongo_url)
            local_db = local_client["mfirme_local"]
            await local_db.command('ping')
            
            # Check if local DB has data
            firme_count = await local_db.firme.count_documents({})
            if firme_count > 0:
                LOCAL_DB_AVAILABLE = True
                print(f"✓ Connected to MongoDB Local ({firme_count:,} firme)")
            else:
                print("⚠ MongoDB Local connected but empty - using cloud")
                LOCAL_DB_AVAILABLE = False
                
        except Exception as e:
            print(f"⚠ Local MongoDB not available, using cloud: {e}")
            LOCAL_DB_AVAILABLE = False
    
    # Set backwards compatibility aliases
    companies_client = cloud_companies_client
    companies_db = get_companies_db()
    
    mode = 'LOCAL + Cloud fallback' if LOCAL_DB_AVAILABLE else 'Cloud only'
    print(f"Database mode: {mode}")


async def close_database_connections():
    global cloud_companies_client, app_client, local_client
    
    if cloud_companies_client:
        cloud_companies_client.close()
    if app_client:
        app_client.close()
    if local_client:
        local_client.close()
    
    print("✓ Closed all MongoDB connections")


def get_companies_db():
    """
    Get the companies database.
    Returns local DB if available and has data, otherwise cloud.
    """
    if LOCAL_DB_AVAILABLE and local_db is not None:
        return local_db
    return cloud_companies_db


def get_readonly_db():
    """Alias for get_companies_db - readonly database with company data"""
    return get_companies_db()


def get_app_db():
    """
    Get the app database (users, settings, etc.)
    Always returns cloud - user data must stay in sync
    """
    return app_db


def get_local_db():
    """Get local database directly (for sync status, etc.)"""
    return local_db


def is_using_local_db() -> bool:
    """Check if currently using local database for reads"""
    return LOCAL_DB_AVAILABLE


async def check_local_db_health() -> dict:
    """Check local database health and sync status"""
    if not local_db:
        return {
            "available": False,
            "reason": "Local DB not configured"
        }
    
    try:
        await local_db.command('ping')
        
        # Get collection counts
        collections = {}
        for col in ['firme', 'bilanturi', 'caen_codes', 'postal_codes', 'localities']:
            try:
                count = await local_db[col].count_documents({})
                collections[col] = count
            except:
                collections[col] = 0
        
        # Get sync status
        sync_status = {}
        try:
            status_docs = await local_db.sync_status.find({}).to_list(length=100)
            for doc in status_docs:
                sync_status[doc['collection']] = {
                    'status': doc.get('status'),
                    'last_sync': doc.get('last_full_sync'),
                    'documents': doc.get('documents_count', 0)
                }
        except:
            pass
        
        return {
            "available": True,
            "using_local": LOCAL_DB_AVAILABLE,
            "collections": collections,
            "sync_status": sync_status,
            "total_documents": sum(collections.values())
        }
        
    except Exception as e:
        return {
            "available": False,
            "reason": str(e)
        }


async def force_use_local(use_local: bool):
    """Force switch between local and cloud database"""
    global LOCAL_DB_AVAILABLE
    
    if use_local and local_db is not None:
        # Verify local DB has data
        firme_count = await local_db.firme.count_documents({})
        if firme_count > 0:
            LOCAL_DB_AVAILABLE = True
            return {"status": "switched_to_local", "firme_count": firme_count}
        else:
            return {"status": "error", "message": "Local DB is empty"}
    else:
        LOCAL_DB_AVAILABLE = False
        return {"status": "switched_to_cloud"}