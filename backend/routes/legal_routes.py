"""
Dosare și BPI Routes - Informații juridice pentru firme
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone
from database import get_local_db
from auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal", tags=["legal"])


@router.get("/dosare/{cui}")
async def get_dosare_by_cui(
    cui: str,
    limit: int = Query(default=50, le=200),
    skip: int = Query(default=0, ge=0)
):
    """
    Get dosare (court cases) for a company by CUI
    First finds firma_id from firme collection, then queries dosare
    """
    local_db = get_local_db()
    
    if local_db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Find firma by CUI to get firma_id
    firma = await local_db.firme.find_one(
        {"$or": [{"cui": cui}, {"cui": int(cui) if cui.isdigit() else cui}]},
        {"id": 1, "denumire": 1}
    )
    
    if not firma:
        return {
            "cui": cui,
            "firma_found": False,
            "total": 0,
            "dosare": []
        }
    
    firma_id = firma.get('id')
    
    if not firma_id:
        return {
            "cui": cui,
            "firma_found": True,
            "firma_id": None,
            "total": 0,
            "dosare": [],
            "message": "Firma nu are ID pentru căutare dosare"
        }
    
    # Count total dosare
    total = await local_db.dosare.count_documents({"firma_id": firma_id})
    
    # Get dosare
    cursor = local_db.dosare.find(
        {"firma_id": firma_id}
    ).sort("data_dosar", -1).skip(skip).limit(limit)
    
    dosare = []
    async for dosar in cursor:
        dosar.pop('_id', None)
        dosare.append({
            "id": dosar.get('id'),
            "numar_dosar": dosar.get('numar_dosar'),
            "data_dosar": dosar.get('data_dosar'),
            "institutie": dosar.get('institutie'),
            "departament": dosar.get('departament'),
            "categorie": dosar.get('categorie_caz') or dosar.get('categorie_caz_nume'),
            "stadiu": dosar.get('stadiu_procesual') or dosar.get('stadiu_procesual_nume'),
            "obiect": dosar.get('obiect'),
            "parti": dosar.get('parti', []),
            "sedinte": dosar.get('sedinte', [])[:5],  # Limit sedinte to last 5
            "calitate_parte": dosar.get('calitate_parte'),
            "data_modificare": dosar.get('data_modificare')
        })
    
    return {
        "cui": cui,
        "firma_found": True,
        "firma_id": firma_id,
        "firma_denumire": firma.get('denumire'),
        "total": total,
        "showing": len(dosare),
        "skip": skip,
        "limit": limit,
        "dosare": dosare
    }


@router.get("/dosare/firma/{firma_id}")
async def get_dosare_by_firma_id(
    firma_id: int,
    limit: int = Query(default=50, le=200),
    skip: int = Query(default=0, ge=0)
):
    """
    Get dosare directly by firma_id
    """
    local_db = get_local_db()
    
    if local_db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    total = await local_db.dosare.count_documents({"firma_id": firma_id})
    
    cursor = local_db.dosare.find(
        {"firma_id": firma_id}
    ).sort("data_dosar", -1).skip(skip).limit(limit)
    
    dosare = []
    async for dosar in cursor:
        dosar.pop('_id', None)
        dosare.append(dosar)
    
    return {
        "firma_id": firma_id,
        "total": total,
        "dosare": dosare
    }


@router.get("/bpi/{cui}")
async def get_bpi_by_cui(
    cui: str,
    limit: int = Query(default=50, le=200),
    skip: int = Query(default=0, ge=0)
):
    """
    Get BPI (Buletinul Procedurilor de Insolvență) records for a company by CUI
    """
    local_db = get_local_db()
    
    if local_db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Normalize CUI
    cui_clean = cui.replace('RO', '').replace(' ', '').strip()
    
    # Search by CUI (try both string and int)
    query = {"$or": [
        {"cui": cui_clean},
        {"cui": int(cui_clean) if cui_clean.isdigit() else cui_clean},
        {"cui": f"RO{cui_clean}"}
    ]}
    
    total = await local_db.bpi_records.count_documents(query)
    
    cursor = local_db.bpi_records.find(query).sort("data_publicare", -1).skip(skip).limit(limit)
    
    records = []
    async for record in cursor:
        record.pop('_id', None)
        records.append({
            "id": record.get('id'),
            "cui": record.get('cui'),
            "denumire_firma": record.get('denumire_firma'),
            "numar_dosar": record.get('dosar') or record.get('numar_dosar'),
            "tip_procedura": record.get('tip_procedura'),
            "etapa_procedura": record.get('etapa_procedura'),
            "data_publicare": record.get('data_publicare'),
            "instanta": record.get('instanta'),
            "practician": record.get('practician') or record.get('lichidator'),
            "descriere": record.get('descriere') or record.get('continut'),
            "sursa": record.get('sursa'),
            "url": record.get('url')
        })
    
    return {
        "cui": cui,
        "total": total,
        "showing": len(records),
        "records": records
    }


@router.get("/lichidatori/{cui}")
async def get_lichidatori_by_cui(cui: str):
    """
    Get lichidatori (liquidators) associated with a company
    """
    local_db = get_local_db()
    
    if local_db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    cui_clean = cui.replace('RO', '').replace(' ', '').strip()
    
    # Search in lichidatori collection where the company appears
    cursor = local_db.lichidatori.find({
        "$or": [
            {"firme.cui": cui_clean},
            {"firme.cui": int(cui_clean) if cui_clean.isdigit() else cui_clean}
        ]
    })
    
    lichidatori = []
    async for lich in cursor:
        lich.pop('_id', None)
        lichidatori.append({
            "id": lich.get('id'),
            "nume": lich.get('nume'),
            "tip": lich.get('tip'),
            "contact": lich.get('contact'),
            "adresa": lich.get('adresa')
        })
    
    return {
        "cui": cui,
        "total": len(lichidatori),
        "lichidatori": lichidatori
    }


@router.get("/summary/{cui}")
async def get_legal_summary(cui: str):
    """
    Get a summary of all legal information for a company.
    Reads pre-computed flags directly from firma document (no extra queries).
    """
    local_db = get_local_db()
    
    if local_db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    cui_clean = cui.replace('RO', '').replace(' ', '').strip()
    
    # Find firma - flags are pre-computed on the document
    firma = await local_db.firme.find_one(
        {"$or": [{"cui": cui_clean}, {"cui": int(cui_clean) if cui_clean.isdigit() else cui_clean}]},
        {"_id": 0, "id": 1, "denumire": 1, "anaf_stare": 1,
         "has_dosare": 1, "dosare_count": 1,
         "has_bpi": 1, "bpi_count": 1,
         "has_legal_issues": 1}
    )
    
    if not firma:
        return {
            "cui": cui,
            "firma_denumire": None,
            "stare": "",
            "dosare_count": 0,
            "bpi_count": 0,
            "in_insolventa": False,
            "has_legal_issues": False
        }
    
    dosare_count = firma.get('dosare_count', 0) or 0
    bpi_count = firma.get('bpi_count', 0) or 0
    stare = firma.get('anaf_stare', '') or ''
    in_insolventa = bpi_count > 0 or 'insolvență' in stare.lower() or 'insolventa' in stare.lower()
    
    return {
        "cui": cui,
        "firma_denumire": firma.get('denumire'),
        "stare": stare,
        "dosare_count": dosare_count,
        "bpi_count": bpi_count,
        "in_insolventa": in_insolventa,
        "has_legal_issues": firma.get('has_legal_issues', False)
    }
