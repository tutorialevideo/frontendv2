"""
Geo Routes - Counties, localities, CAEN top, platform stats
Extracted from server.py
"""

from fastapi import APIRouter, Query
from database import get_companies_db
from typing import Optional
from urllib.parse import unquote

router = APIRouter(prefix="/api", tags=["geo"])


@router.get("/geo/judete")
async def get_judete():
    """Get list of all counties (judete)"""
    db = get_companies_db()

    pipeline = [
        {"$group": {"_id": "$judet", "count": {"$sum": 1}}},
        {"$match": {"_id": {"$ne": None}}},
        {"$sort": {"_id": 1}},
        {"$project": {"judet": "$_id", "count": 1, "_id": 0}},
    ]

    judete = await db.firme.aggregate(pipeline).to_list(length=100)
    return {"judete": judete}


@router.get("/geo/localitati")
async def get_localitati(judet: Optional[str] = None):
    """Get list of localities, optionally filtered by county, sorted by company count"""
    db = get_companies_db()

    match_stage = {}
    if judet:
        match_stage["judet"] = unquote(judet)

    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {"localitate": {"$ne": None}}},
        {"$group": {
            "_id": {"localitate": "$localitate", "judet": "$judet"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
        {"$limit": 500},
        {"$project": {
            "localitate": "$_id.localitate",
            "judet": "$_id.judet",
            "count": 1,
            "_id": 0,
        }},
    ]

    localitati = await db.firme.aggregate(pipeline).to_list(length=500)
    return {"localitati": localitati}


@router.get("/caen/top")
async def get_top_caen_codes(limit: int = Query(50, ge=1, le=200)):
    """Get top CAEN codes by company count"""
    db = get_companies_db()

    pipeline = [
        {"$match": {"anaf_cod_caen": {"$ne": None}}},
        {"$group": {"_id": "$anaf_cod_caen", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"caen": "$_id", "count": 1, "_id": 0}},
    ]

    caen_codes = await db.firme.aggregate(pipeline).to_list(length=limit)
    return {"caen_codes": caen_codes}


@router.get("/stats/overview")
async def get_platform_stats():
    """Get platform overview statistics"""
    db = get_companies_db()

    total_companies = await db.firme.count_documents({})
    active_companies = await db.firme.count_documents({"anaf_inactiv": {"$ne": True}})
    judete_count = len(await db.firme.distinct("judet"))
    with_financials = await db.firme.count_documents({"mf_cifra_afaceri": {"$gt": 0}})

    return {
        "total_companies": total_companies,
        "active_companies": active_companies,
        "counties": judete_count,
        "with_financials": with_financials,
    }
