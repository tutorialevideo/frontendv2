"""
Sitemap Generator - Dynamic XML sitemap generation for 2M+ companies
Generates paginated sitemaps: companies, judete, localitati, CAEN codes
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import Response
from database import get_local_db, get_app_db
from auth import get_current_user
from datetime import datetime, timezone
import re
import unicodedata
import logging
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sitemap", tags=["sitemap"])

SITE_URL = "https://mfirme.ro"
MAX_URLS_PER_SITEMAP = 45000


def make_slug(text):
    if not text:
        return ""
    replacements = {'ş': 'ș', 'Ş': 'Ș', 'ţ': 'ț', 'Ţ': 'Ț'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


def require_admin(current_user=Depends(get_current_user)):
    if not current_user or current_user.get('role') != 'admin':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin required")
    return current_user


# ---- SITEMAP INDEX ----

@router.get("/index.xml")
async def sitemap_index():
    """Dynamic sitemap index listing all sub-sitemaps"""
    db = get_local_db()
    app_db = get_app_db()

    # Get generation status
    status = await app_db.sitemap_status.find_one({"type": "generation"}, {"_id": 0})

    total_companies = await db.firme.count_documents({"anaf_stare_startswith_inregistrat": True, "cui": {"$exists": True, "$ne": None}})
    company_pages = math.ceil(total_companies / MAX_URLS_PER_SITEMAP)

    lastmod = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if status and status.get('last_generated'):
        lastmod = status['last_generated'].strftime('%Y-%m-%d')

    sitemaps = []
    sitemaps.append(f'  <sitemap><loc>{SITE_URL}/api/sitemap/static.xml</loc><lastmod>{lastmod}</lastmod></sitemap>')
    sitemaps.append(f'  <sitemap><loc>{SITE_URL}/api/sitemap/judete.xml</loc><lastmod>{lastmod}</lastmod></sitemap>')
    sitemaps.append(f'  <sitemap><loc>{SITE_URL}/api/sitemap/caen.xml</loc><lastmod>{lastmod}</lastmod></sitemap>')

    for i in range(1, company_pages + 1):
        sitemaps.append(f'  <sitemap><loc>{SITE_URL}/api/sitemap/companies-{i}.xml</loc><lastmod>{lastmod}</lastmod></sitemap>')

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemaps)}
</sitemapindex>'''

    return Response(content=xml, media_type="application/xml")


# ---- STATIC PAGES ----

@router.get("/static.xml")
async def sitemap_static():
    """Static pages sitemap"""
    pages = [
        ('/', '1.0', 'daily'),
        ('/search', '0.8', 'daily'),
        ('/judete', '0.8', 'weekly'),
        ('/caen', '0.8', 'weekly'),
    ]

    urls = []
    for path, priority, freq in pages:
        urls.append(f'''  <url>
    <loc>{SITE_URL}{path}</loc>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>''')

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''

    return Response(content=xml, media_type="application/xml")


# ---- JUDETE + LOCALITATI ----

@router.get("/judete.xml")
async def sitemap_judete():
    """Judete and localities sitemap"""
    db = get_local_db()

    pipeline = [
        {"$match": {"judet": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$judet"}},
        {"$sort": {"_id": 1}}
    ]

    urls = []
    judete_slugs = set()

    async for doc in db.firme.aggregate(pipeline):
        judet = doc["_id"]
        slug = make_slug(judet)
        if slug and slug not in judete_slugs:
            judete_slugs.add(slug)
            urls.append(f'''  <url>
    <loc>{SITE_URL}/judet/{slug}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>''')

    # Add top localities per judet
    loc_pipeline = [
        {"$match": {"judet": {"$exists": True, "$ne": None}, "localitate": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": {"judet": "$judet", "localitate": "$localitate"}, "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 10}}},
        {"$sort": {"count": -1}},
        {"$limit": 5000}
    ]

    async for doc in db.firme.aggregate(loc_pipeline):
        judet_slug = make_slug(doc["_id"]["judet"])
        loc_slug = make_slug(doc["_id"]["localitate"])
        if judet_slug and loc_slug:
            urls.append(f'''  <url>
    <loc>{SITE_URL}/judet/{judet_slug}/{loc_slug}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>''')

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''

    return Response(content=xml, media_type="application/xml")


# ---- CAEN CODES ----

@router.get("/caen.xml")
async def sitemap_caen():
    """CAEN codes sitemap"""
    db = get_local_db()

    pipeline = [
        {"$match": {"anaf_cod_caen": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$anaf_cod_caen", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 5}}},
        {"$sort": {"count": -1}}
    ]

    urls = []
    async for doc in db.firme.aggregate(pipeline):
        cod = doc["_id"]
        urls.append(f'''  <url>
    <loc>{SITE_URL}/caen/{cod}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>''')

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''

    return Response(content=xml, media_type="application/xml")


# ---- COMPANIES (PAGINATED) ----

@router.get("/companies-{page_num}.xml")
async def sitemap_companies(page_num: int):
    """Paginated company sitemap - 45K URLs per page"""
    db = get_local_db()

    if page_num < 1:
        return Response(content="<error>Invalid page</error>", media_type="application/xml", status_code=400)

    skip = (page_num - 1) * MAX_URLS_PER_SITEMAP
    projection = {"_id": 0, "cui": 1, "denumire": 1}

    cursor = db.firme.find(
        {"anaf_stare_startswith_inregistrat": True, "cui": {"$exists": True, "$ne": None}},
        projection
    ).skip(skip).limit(MAX_URLS_PER_SITEMAP)

    urls = []
    async for firma in cursor:
        cui = firma.get("cui", "")
        denumire = firma.get("denumire", "")
        slug = make_slug(denumire) + "-" + str(cui) if cui else make_slug(denumire)
        if slug:
            urls.append(f'  <url><loc>{SITE_URL}/firma/{slug}</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>')

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''

    return Response(content=xml, media_type="application/xml")


# ---- ADMIN: GENERATION STATUS & TRIGGER ----

@router.get("/status")
async def get_sitemap_status(current_user=Depends(require_admin)):
    """Get sitemap generation status and stats"""
    db = get_local_db()
    app_db = get_app_db()

    status = await app_db.sitemap_status.find_one({"type": "generation"}, {"_id": 0})

    total_active = await db.firme.count_documents({"anaf_stare_startswith_inregistrat": True, "cui": {"$exists": True, "$ne": None}})
    company_pages = math.ceil(total_active / MAX_URLS_PER_SITEMAP)

    judete_count = len(await db.firme.distinct("judet"))
    caen_count = len(await db.firme.distinct("anaf_cod_caen"))

    loc_pipeline = [
        {"$match": {"judet": {"$exists": True, "$ne": None}, "localitate": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": {"judet": "$judet", "localitate": "$localitate"}, "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 10}}},
        {"$count": "total"}
    ]
    loc_result = await db.firme.aggregate(loc_pipeline).to_list(1)
    loc_count = loc_result[0]["total"] if loc_result else 0

    return {
        "last_generated": status.get("last_generated").isoformat() if status and status.get("last_generated") else None,
        "generating": status.get("generating", False) if status else False,
        "stats": {
            "company_pages": company_pages,
            "total_active_companies": total_active,
            "urls_per_page": MAX_URLS_PER_SITEMAP,
            "judete": judete_count,
            "localitati": loc_count,
            "caen_codes": caen_count,
            "total_sitemaps": company_pages + 3,
            "estimated_total_urls": total_active + loc_count + caen_count + judete_count + 4
        }
    }


@router.post("/generate")
async def trigger_sitemap_generation(
    background_tasks: BackgroundTasks,
    current_user=Depends(require_admin)
):
    """Mark sitemap as regenerated (sitemaps are dynamic, this updates the timestamp)"""
    app_db = get_app_db()

    await app_db.sitemap_status.update_one(
        {"type": "generation"},
        {"$set": {
            "type": "generation",
            "last_generated": datetime.now(timezone.utc),
            "generated_by": current_user.get("email"),
            "generating": False
        }},
        upsert=True
    )

    return {"message": "Sitemap timestamp updated. All sitemaps are generated dynamically on request."}
