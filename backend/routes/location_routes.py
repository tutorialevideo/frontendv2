"""
Location Routes - Browse companies by Judet/Localitate (SIRUTA hierarchy)
"""
from fastapi import APIRouter, Query
from database import get_local_db
import re
import unicodedata

router = APIRouter(prefix="/api/locations", tags=["locations"])


def normalize_diacritics(text):
    """Normalize Romanian diacritics: ş->ș, ţ->ț, etc."""
    if not text:
        return text
    replacements = {
        'ş': 'ș', 'Ş': 'Ș',
        'ţ': 'ț', 'Ţ': 'Ț',
        'ã': 'ă', 'Ã': 'Ă',
        'î': 'î', 'Î': 'Î',
        'â': 'â', 'Â': 'Â',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def make_slug(text):
    """Create URL-friendly slug from Romanian text"""
    if not text:
        return ""
    text = normalize_diacritics(text)
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


def clean_localitate(loc):
    """Clean localitate name: remove prefixes like 'Loc.', 'Sat', 'Municipiul', 'Oraș' etc."""
    if not loc:
        return loc
    loc = normalize_diacritics(loc)
    loc = re.sub(r'^(Loc\.\s*|Sat\s+|Comuna\s+|Municipiul\s+|Orașul\s+|Oraş\s+|Oraș\s+)', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r',\s*(Oraș|Oraş|Comuna|Municipiul|Sat)\s+.*$', '', loc, flags=re.IGNORECASE)
    return loc.strip()


# Pre-built mapping for judet normalization
JUDET_NORMALIZE = {}


async def get_judet_groups(db):
    """Get judete grouped with normalized names"""
    pipeline = [
        {"$match": {"judet": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$judet", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]

    groups = {}
    async for doc in db.firme.aggregate(pipeline):
        raw = doc["_id"]
        normalized = normalize_diacritics(raw)
        slug = make_slug(normalized)

        if slug not in groups:
            groups[slug] = {"name": normalized, "slug": slug, "count": 0, "raw_names": []}
        groups[slug]["count"] += doc["count"]
        groups[slug]["raw_names"].append(raw)

    return groups


@router.get("/judete")
async def list_judete():
    """List all Romanian counties with company counts"""
    db = get_local_db()
    groups = await get_judet_groups(db)

    judete = sorted(groups.values(), key=lambda x: x["name"] or "")
    return {
        "total": len(judete),
        "judete": [{"name": j["name"], "slug": j["slug"], "company_count": j["count"]} for j in judete if j["name"]]
    }


@router.get("/judet/{judet_slug}")
async def get_judet_localities(
    judet_slug: str,
    skip: int = 0,
    limit: int = 100
):
    """List all localities in a county with company counts"""
    db = get_local_db()
    groups = await get_judet_groups(db)

    if judet_slug not in groups:
        return {"error": "Judet not found", "judet_slug": judet_slug}

    judet_info = groups[judet_slug]
    raw_names = judet_info["raw_names"]

    pipeline = [
        {"$match": {"judet": {"$in": raw_names}, "localitate": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {
            "_id": "$localitate",
            "count": {"$sum": 1},
            "siruta": {"$first": "$siruta"}
        }},
        {"$sort": {"count": -1}}
    ]

    raw_localities = {}
    async for doc in db.firme.aggregate(pipeline):
        raw_name = doc["_id"]
        cleaned = clean_localitate(raw_name)
        slug = make_slug(cleaned)

        if not slug:
            continue

        if slug not in raw_localities:
            raw_localities[slug] = {
                "name": cleaned,
                "slug": slug,
                "company_count": 0,
                "siruta": doc.get("siruta"),
                "raw_names": []
            }
        raw_localities[slug]["company_count"] += doc["count"]
        raw_localities[slug]["raw_names"].append(raw_name)

    localities = sorted(raw_localities.values(), key=lambda x: -x["company_count"])
    total = len(localities)
    page = localities[skip:skip+limit]

    return {
        "judet": judet_info["name"],
        "judet_slug": judet_slug,
        "total_localities": total,
        "total_companies": judet_info["count"],
        "localities": [
            {"name": l["name"], "slug": l["slug"], "company_count": l["company_count"], "siruta": l.get("siruta")}
            for l in page
        ]
    }


@router.get("/judet/{judet_slug}/{localitate_slug}")
async def get_locality_companies(
    judet_slug: str,
    localitate_slug: str,
    skip: int = 0,
    limit: int = 50,
    q: str = ""
):
    """List companies in a specific locality"""
    db = get_local_db()
    groups = await get_judet_groups(db)

    if judet_slug not in groups:
        return {"error": "Judet not found"}

    judet_info = groups[judet_slug]
    raw_judet_names = judet_info["raw_names"]

    # Find matching localities
    pipeline = [
        {"$match": {"judet": {"$in": raw_judet_names}, "localitate": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$localitate", "count": {"$sum": 1}}}
    ]

    matching_raw_names = []
    locality_name = ""
    async for doc in db.firme.aggregate(pipeline):
        raw_name = doc["_id"]
        cleaned = clean_localitate(raw_name)
        slug = make_slug(cleaned)
        if slug == localitate_slug:
            matching_raw_names.append(raw_name)
            if not locality_name:
                locality_name = cleaned

    if not matching_raw_names:
        return {"error": "Locality not found"}

    # Build query
    query = {"judet": {"$in": raw_judet_names}, "localitate": {"$in": matching_raw_names}}
    if q.strip():
        if q.isdigit():
            query["cui"] = q
        else:
            query["denumire"] = {"$regex": q, "$options": "i"}

    total = await db.firme.count_documents(query)

    projection = {
        "_id": 0, "cui": 1, "denumire": 1, "judet": 1, "localitate": 1,
        "forma_juridica": 1, "anaf_stare": 1, "anaf_cod_caen": 1,
        "caen_description": 1, "mf_cifra_afaceri": 1, "mf_numar_angajati": 1,
        "mf_an_bilant": 1, "has_dosare": 1, "dosare_count": 1,
        "has_bpi": 1, "has_legal_issues": 1,
        "anaf_stare_startswith_inregistrat": 1
    }

    cursor = db.firme.find(query, projection).skip(skip).limit(limit)

    # Build slug for each company
    companies = []
    async for c in cursor:
        den = c.get("denumire", "")
        cui = c.get("cui", "")
        slug = make_slug(den) + "-" + cui if cui else make_slug(den)
        c["slug"] = slug
        companies.append(c)

    return {
        "judet": judet_info["name"],
        "judet_slug": judet_slug,
        "localitate": locality_name,
        "localitate_slug": localitate_slug,
        "total": total,
        "skip": skip,
        "limit": limit,
        "companies": companies
    }
