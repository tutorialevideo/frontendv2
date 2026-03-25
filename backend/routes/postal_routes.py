"""
Postal codes API routes
Provides postal code lookup and matching for Romanian companies
"""

from fastapi import APIRouter, HTTPException, Query
from database import get_app_db, get_companies_db
from typing import Optional
import re

router = APIRouter(prefix="/api/postal", tags=["postal"])

def normalize_text(text):
    """Normalize text for matching (remove diacritics, uppercase, prefixes)"""
    if not text:
        return ""
    
    replacements = {
        'ş': 's', 'Ş': 'S', 'ș': 's', 'Ș': 'S',
        'ţ': 't', 'Ţ': 'T', 'ț': 't', 'Ț': 'T',
        'ă': 'a', 'Ă': 'A',
        'â': 'a', 'Â': 'A',
        'î': 'i', 'Î': 'I'
    }
    
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    # Remove text in parentheses
    result = re.sub(r'\([^)]*\)', '', result).strip()
    
    # Remove common prefixes from locality names (for firme database)
    prefixes_to_remove = [
        'MUNICIPIUL ', 'MUN. ', 'MUN ',
        'ORASUL ', 'ORAS ', 'OR. ', 'OR ',
        'COMUNA ', 'COM. ', 'COM ',
        'SATUL ', 'SAT ', 'S. ',
        'SECTOR '
    ]
    
    upper_result = result.upper()
    for prefix in prefixes_to_remove:
        if upper_result.startswith(prefix):
            upper_result = upper_result[len(prefix):].strip()
            break
    
    return upper_result


@router.get("/search")
async def search_postal_codes(
    cod: Optional[str] = Query(None, description="Postal code to search"),
    localitate: Optional[str] = Query(None, description="Locality name"),
    judet: Optional[str] = Query(None, description="County name"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search postal codes by code, locality, or county
    """
    db = get_app_db()
    
    query = {}
    
    if cod:
        query["cod_postal"] = {"$regex": f"^{re.escape(cod)}"}
    
    if localitate:
        normalized = normalize_text(localitate)
        query["localitate_normalized"] = {"$regex": f"^{re.escape(normalized)}"}
    
    if judet:
        normalized = normalize_text(judet)
        query["judet_normalized"] = normalized
    
    if not query:
        raise HTTPException(status_code=400, detail="At least one search parameter required")
    
    results = await db.postal_codes.find(
        query,
        {"_id": 0, "id": 0, "judet_normalized": 0, "localitate_normalized": 0}
    ).limit(limit).to_list(length=limit)
    
    return {
        "results": results,
        "count": len(results)
    }


@router.get("/localities")
async def get_localities(
    judet: Optional[str] = Query(None, description="Filter by county"),
    search: Optional[str] = Query(None, description="Search locality name"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get unique localities with their postal codes
    """
    db = get_app_db()
    
    query = {}
    
    if judet:
        normalized = normalize_text(judet)
        query["judet_normalized"] = normalized
    
    if search:
        normalized = normalize_text(search)
        query["localitate_normalized"] = {"$regex": f"^{re.escape(normalized)}"}
    
    results = await db.localities.find(
        query,
        {"_id": 0, "judet_normalized": 0, "localitate_normalized": 0}
    ).limit(limit).to_list(length=limit)
    
    return {
        "localities": results,
        "count": len(results)
    }


@router.get("/match/company/{cui}")
async def match_company_postal_code(cui: str):
    """
    Find postal code for a company based on its address
    """
    companies_db = get_companies_db()
    app_db = get_app_db()
    
    # Normalize CUI
    normalized_cui = cui.lstrip('0').upper().replace('RO', '')
    
    # Get company
    company = await companies_db.firme.find_one({"cui": normalized_cui})
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    judet = company.get('judet', '')
    localitate = company.get('localitate', '')
    adresa = company.get('adresa', '')
    
    if not judet or not localitate:
        return {
            "company": {
                "cui": normalized_cui,
                "denumire": company.get('denumire'),
                "judet": judet,
                "localitate": localitate,
                "adresa": adresa
            },
            "match": None,
            "message": "Company has incomplete address data"
        }
    
    # Normalize for matching
    judet_norm = normalize_text(judet)
    localitate_norm = normalize_text(localitate)
    
    # Try to find matching locality
    locality_match = await app_db.localities.find_one({
        "judet_normalized": judet_norm,
        "localitate_normalized": localitate_norm
    })
    
    if locality_match:
        return {
            "company": {
                "cui": normalized_cui,
                "denumire": company.get('denumire'),
                "judet": judet,
                "localitate": localitate,
                "adresa": adresa
            },
            "match": {
                "judet": locality_match.get('judet'),
                "localitate": locality_match.get('localitate'),
                "postal_codes": locality_match.get('postal_codes', []),
                "primary_postal_code": locality_match.get('primary_postal_code'),
                "match_type": "exact"
            }
        }
    
    # Try fuzzy match - search for localities starting with same prefix
    fuzzy_matches = await app_db.localities.find({
        "judet_normalized": judet_norm,
        "localitate_normalized": {"$regex": f"^{re.escape(localitate_norm[:5])}"}
    }).limit(5).to_list(length=5)
    
    if fuzzy_matches:
        return {
            "company": {
                "cui": normalized_cui,
                "denumire": company.get('denumire'),
                "judet": judet,
                "localitate": localitate,
                "adresa": adresa
            },
            "match": None,
            "suggestions": [
                {
                    "judet": m.get('judet'),
                    "localitate": m.get('localitate'),
                    "primary_postal_code": m.get('primary_postal_code')
                }
                for m in fuzzy_matches
            ],
            "message": "No exact match found, but similar localities exist"
        }
    
    return {
        "company": {
            "cui": normalized_cui,
            "denumire": company.get('denumire'),
            "judet": judet,
            "localitate": localitate,
            "adresa": adresa
        },
        "match": None,
        "message": "No postal code match found for this locality"
    }


@router.get("/stats")
async def get_postal_stats():
    """
    Get statistics about postal codes database
    """
    db = get_app_db()
    
    total_codes = await db.postal_codes.count_documents({})
    total_localities = await db.localities.count_documents({})
    
    # Get counties count
    counties = await db.postal_codes.distinct("judet")
    
    return {
        "total_postal_codes": total_codes,
        "total_localities": total_localities,
        "total_counties": len(counties),
        "counties": sorted(counties)
    }


@router.get("/by-code/{cod_postal}")
async def get_by_postal_code(cod_postal: str):
    """
    Get location details by postal code
    """
    db = get_app_db()
    
    results = await db.postal_codes.find(
        {"cod_postal": cod_postal},
        {"_id": 0, "id": 0, "judet_normalized": 0, "localitate_normalized": 0}
    ).to_list(length=100)
    
    if not results:
        raise HTTPException(status_code=404, detail="Postal code not found")
    
    # Get unique locality info
    localities = list(set((r.get('judet'), r.get('localitate')) for r in results))
    
    return {
        "cod_postal": cod_postal,
        "locations": [
            {"judet": j, "localitate": l} for j, l in localities
        ],
        "details": results
    }
