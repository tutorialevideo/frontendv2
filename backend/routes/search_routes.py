"""
Search Routes - Company search and autocomplete
Extracted from server.py
"""

from fastapi import APIRouter, Query
from database import get_companies_db
from utils import compute_company_profile, create_company_slug
from typing import Optional
from urllib.parse import unquote
import re

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search/suggest")
async def search_suggest(q: str = Query(..., min_length=2)):
    """Autocomplete suggestions for search"""
    db = get_companies_db()

    pattern = re.compile(f"^{re.escape(q)}", re.IGNORECASE)
    cui_pattern = re.compile(f"^{re.escape(q)}")

    suggestions = []

    name_results = await db.firme.find(
        {"denumire": {"$regex": pattern}},
        {"denumire": 1, "cui": 1, "judet": 1, "localitate": 1},
    ).limit(5).to_list(length=5)

    for result in name_results:
        suggestions.append({
            "type": "company",
            "label": result["denumire"],
            "cui": result.get("cui"),
            "location": f"{result.get('localitate', '')}, {result.get('judet', '')}",
            "slug": create_company_slug(result["denumire"], result.get("cui", "")),
        })

    if q.isdigit() and len(suggestions) < 10:
        cui_results = await db.firme.find(
            {"cui": {"$regex": cui_pattern}},
            {"denumire": 1, "cui": 1, "judet": 1, "localitate": 1},
        ).limit(5).to_list(length=5)

        for result in cui_results:
            if result["cui"] not in [s.get("cui") for s in suggestions]:
                suggestions.append({
                    "type": "company",
                    "label": result["denumire"],
                    "cui": result.get("cui"),
                    "location": f"{result.get('localitate', '')}, {result.get('judet', '')}",
                    "slug": create_company_slug(result["denumire"], result.get("cui", "")),
                })

    return {"suggestions": suggestions[:10]}


@router.get("/search")
async def search_companies(
    q: Optional[str] = None,
    judet: Optional[str] = None,
    localitate: Optional[str] = None,
    caen: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Search companies with filters"""
    db = get_companies_db()

    query = {}

    if q:
        if q.isdigit():
            # CUI might be stored as string or int — search both
            query["$or"] = [
                {"cui": q},
                {"cui": int(q)},
                {"cui": {"$regex": f"^{re.escape(q)}"}},
            ]
        else:
            query["denumire"] = {"$regex": re.escape(q), "$options": "i"}

    if judet:
        query["judet"] = unquote(judet)

    if localitate:
        query["localitate"] = {"$regex": f"^{re.escape(unquote(localitate))}", "$options": "i"}

    if caen:
        query["anaf_cod_caen"] = {"$regex": f"^{re.escape(caen)}"}

    total = await db.firme.count_documents(query)

    skip = (page - 1) * limit
    results = await db.firme.find(query).skip(skip).limit(limit).to_list(length=limit)

    companies = []
    for result in results:
        profile = compute_company_profile(result, tier="public")
        companies.append({
            "slug": profile["slug"],
            "cui": result.get("cui"),
            "denumire": result.get("denumire"),
            "judet": result.get("judet"),
            "localitate": result.get("localitate"),
            "forma_juridica": result.get("forma_juridica"),
            "anaf_stare": result.get("anaf_stare"),
            "anaf_cod_caen": result.get("anaf_cod_caen"),
            "mf_cifra_afaceri": result.get("mf_cifra_afaceri"),
            "mf_numar_angajati": result.get("mf_numar_angajati"),
            "mf_an_bilant": result.get("mf_an_bilant"),
            "anaf_telefon": result.get("anaf_telefon"),
            "anaf_fax": result.get("anaf_fax"),
        })

    return {
        "results": companies,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "limit": limit,
    }
