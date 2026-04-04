from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import connect_to_databases, close_database_connections
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_databases()
    # Pre-warm caches in background (non-blocking)
    import asyncio
    async def _warm_caches():
        try:
            await asyncio.sleep(2)
            from database import get_local_db
            from routes.location_routes import get_judet_groups
            from routes.caen_routes import _get_caen_counts
            db = get_local_db()
            if db is not None:
                logger.info("Pre-warming judet cache...")
                await get_judet_groups(db)
                logger.info("Pre-warming CAEN cache...")
                await _get_caen_counts(db)
                logger.info("Caches pre-warmed successfully")
        except Exception as e:
            logger.warning(f"Cache pre-warm failed (non-critical): {e}")
    asyncio.create_task(_warm_caches())
    yield
    # Shutdown
    await close_database_connections()

app = FastAPI(title="RapoarteFirme API", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include all routers ──────────────────────────────────────────────────
from routes.auth_routes import router as auth_router
from routes.user_routes import router as user_router
from routes.subscription_routes import router as subscription_router
from routes.admin_routes import router as admin_router
from routes.admin_companies_routes import router as admin_companies_router
from routes.admin_users_routes import router as admin_users_router
from routes.admin_audit_routes import router as admin_audit_router
from routes.postal_routes import router as postal_router
from routes.credits_routes import router as credits_router
from routes.admin_sync_routes import router as admin_sync_router
from routes.api_keys_routes import router as api_keys_router
from routes.public_api_routes import router as public_api_router
from routes.elasticsearch_routes import router as elasticsearch_router
from routes.seo_routes import router as seo_router
from routes.financial_routes import router as financial_router
from routes.legal_routes import router as legal_router
from routes.location_routes import router as location_router
from routes.caen_routes import router as caen_router
from routes.sitemap_routes import router as sitemap_router
from routes.admin_db_routes import router as admin_db_router
from routes.search_routes import router as search_router
from routes.company_routes import router as company_router
from routes.geo_routes import router as geo_router
from routes.seo_gen_routes import router as seo_gen_router

for r in [
    auth_router, user_router, subscription_router,
    admin_router, admin_companies_router, admin_users_router, admin_audit_router,
    postal_router, credits_router, admin_sync_router,
    api_keys_router, public_api_router, elasticsearch_router,
    seo_router, financial_router, legal_router,
    location_router, caen_router, sitemap_router, admin_db_router,
    search_router, company_router, geo_router, seo_gen_router,
]:
    app.include_router(r)

# ── Sitemap URL aliases (production nginx proxies /sitemap*.xml → backend) ──
from routes.sitemap_routes import (
    sitemap_index, sitemap_static, sitemap_judete,
    sitemap_caen, sitemap_companies,
)

@app.get("/api/sitemap.xml")
async def sitemap_xml_root():
    return await sitemap_index()

@app.get("/api/sitemap-static.xml")
async def sitemap_static_root():
    return await sitemap_static()

@app.get("/api/sitemap-judete.xml")
async def sitemap_judete_root():
    return await sitemap_judete()

@app.get("/api/sitemap-caen.xml")
async def sitemap_caen_root():
    return await sitemap_caen()

@app.get("/api/sitemap-companies-{page_num}.xml")
async def sitemap_companies_root(page_num: int):
    return await sitemap_companies(page_num)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "RapoarteFirme API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
