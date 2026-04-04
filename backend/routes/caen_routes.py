"""
CAEN Routes - Browse companies by CAEN activity code
"""
from fastapi import APIRouter, Query
from database import get_local_db
import time

router = APIRouter(prefix="/api/caen", tags=["caen"])

# Cache for CAEN company counts (expensive aggregation)
_caen_counts_cache = {"data": None, "timestamp": 0}
_CACHE_TTL = 3600  # 1 hour


async def _get_caen_counts(db):
    """Get company counts per CAEN code (cached 1h)"""
    now = time.time()
    if _caen_counts_cache["data"] and (now - _caen_counts_cache["timestamp"]) < _CACHE_TTL:
        return _caen_counts_cache["data"]

    pipeline = [
        {"$match": {"anaf_cod_caen": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$anaf_cod_caen", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = {}
    async for doc in db.firme.aggregate(pipeline):
        result[str(doc["_id"])] = doc["count"]

    _caen_counts_cache["data"] = result
    _caen_counts_cache["timestamp"] = now
    return result


@router.get("/codes")
async def list_caen_codes(
    sectiune: str = "",
    q: str = ""
):
    """List all CAEN codes with company counts, optionally filtered by section or search"""
    db = get_local_db()

    # Get CAEN codes from collection
    caen_query = {}
    if sectiune:
        caen_query["sectiune"] = sectiune
    if q.strip():
        caen_query["$or"] = [
            {"cod": {"$regex": q, "$options": "i"}},
            {"denumire": {"$regex": q, "$options": "i"}}
        ]

    caen_codes = {}
    async for doc in db.caen_codes.find(caen_query, {"_id": 0}):
        caen_codes[doc["cod"]] = {
            "cod": doc["cod"],
            "denumire": doc.get("denumire", ""),
            "sectiune": doc.get("sectiune", ""),
            "sectiune_denumire": doc.get("sectiune_denumire", ""),
            "company_count": 0
        }

    # Get cached company counts per CAEN
    counts = await _get_caen_counts(db)
    for cod, count in counts.items():
        if cod in caen_codes:
            caen_codes[cod]["company_count"] = count
        elif not sectiune and not q:
            caen_codes[cod] = {
                "cod": cod,
                "denumire": "",
                "sectiune": "",
                "sectiune_denumire": "",
                "company_count": count
            }

    codes = sorted(caen_codes.values(), key=lambda x: -x["company_count"])

    return {
        "total": len(codes),
        "codes": codes
    }


@router.get("/sections")
async def list_caen_sections():
    """List all CAEN sections (A, B, C, etc.)"""
    db = get_local_db()

    pipeline = [
        {"$match": {"sectiune": {"$exists": True, "$ne": None}}},
        {"$group": {
            "_id": "$sectiune",
            "denumire": {"$first": "$sectiune_denumire"},
            "codes_count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    sections = []
    async for doc in db.caen_codes.aggregate(pipeline):
        sections.append({
            "sectiune": doc["_id"],
            "denumire": doc.get("denumire", ""),
            "codes_count": doc["codes_count"]
        })

    return {"total": len(sections), "sections": sections}


@router.get("/code/{cod}")
async def get_caen_companies(
    cod: str,
    skip: int = 0,
    limit: int = 50,
    q: str = "",
    judet: str = "",
    sort: str = "cifra_afaceri"
):
    """Get companies by CAEN code with pagination and filters"""
    db = get_local_db()

    # Get CAEN info
    caen_info = await db.caen_codes.find_one({"cod": cod}, {"_id": 0})
    if not caen_info:
        caen_info = {"cod": cod, "denumire": "", "sectiune": ""}

    # Build query
    query = {"anaf_cod_caen": cod}
    if q.strip():
        if q.isdigit():
            query["cui"] = q
        else:
            query["denumire"] = {"$regex": q, "$options": "i"}
    if judet.strip():
        query["judet"] = {"$regex": judet, "$options": "i"}

    total = await db.firme.count_documents(query)

    projection = {
        "_id": 0, "cui": 1, "denumire": 1, "judet": 1, "localitate": 1,
        "anaf_cod_caen": 1, "caen_description": 1, "forma_juridica": 1,
        "anaf_stare": 1, "anaf_stare_startswith_inregistrat": 1,
        "mf_cifra_afaceri": 1, "mf_numar_angajati": 1, "mf_an_bilant": 1,
        "has_dosare": 1, "dosare_count": 1, "has_legal_issues": 1
    }

    # Sort
    if sort == "cifra_afaceri":
        sort_spec = [("mf_cifra_afaceri", -1)]
    elif sort == "angajati":
        sort_spec = [("mf_numar_angajati", -1)]
    elif sort == "alfabetic":
        sort_spec = [("denumire", 1)]
    else:
        sort_spec = [("mf_cifra_afaceri", -1)]

    cursor = db.firme.find(query, projection).sort(sort_spec).skip(skip).limit(limit)

    companies = []
    async for c in cursor:
        den = c.get("denumire", "")
        cui = c.get("cui", "")
        import re, unicodedata
        slug_text = den.lower()
        diacritics = {'ş':'s','ș':'s','ţ':'t','ț':'t','ă':'a','â':'a','î':'i'}
        for k, v in diacritics.items():
            slug_text = slug_text.replace(k, v)
        slug_text = unicodedata.normalize('NFD', slug_text)
        slug_text = ''.join(ch for ch in slug_text if unicodedata.category(ch) != 'Mn')
        slug_text = re.sub(r'[^a-z0-9\s-]', '', slug_text)
        slug_text = re.sub(r'[\s-]+', '-', slug_text).strip('-')
        c["slug"] = f"{slug_text}-{cui}" if cui else slug_text
        companies.append(c)

    # Get top judete for this CAEN
    judete_pipeline = [
        {"$match": {"anaf_cod_caen": cod, "judet": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$judet", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_judete = []
    async for doc in db.firme.aggregate(judete_pipeline):
        top_judete.append({"judet": doc["_id"], "count": doc["count"]})

    return {
        "caen": caen_info,
        "total": total,
        "skip": skip,
        "limit": limit,
        "companies": companies,
        "top_judete": top_judete
    }
