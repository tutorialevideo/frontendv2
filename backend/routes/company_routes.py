"""
Company Routes - Company profile, slug lookup, financials
Extracted from server.py
"""

from fastapi import APIRouter, HTTPException, Depends
from database import get_companies_db, get_app_db
from utils import compute_company_profile, serialize_doc, normalize_cui
from auth import get_current_user_optional
import re

router = APIRouter(prefix="/api", tags=["company"])


async def _find_postal_code(app_db, judet: str, localitate: str) -> str:
    """Find postal code for a company based on judet and localitate"""
    if not judet or not localitate:
        return None

    def normalize_text(text, is_bucuresti=False):
        if not text:
            return ""
        replacements = {
            'ş': 's', 'Ş': 'S', 'ș': 's', 'Ș': 'S',
            'ţ': 't', 'Ţ': 'T', 'ț': 't', 'Ț': 'T',
            'ă': 'a', 'Ă': 'A', 'â': 'a', 'Â': 'A',
            'î': 'i', 'Î': 'I',
        }
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        result = re.sub(r'\([^)]*\)', '', result).strip()
        upper_result = result.upper()
        if is_bucuresti:
            sector_match = re.search(r'SECTOR(?:UL)?\s*(\d)', upper_result)
            if sector_match:
                return f"SECTOR{sector_match.group(1)}"
        prefixes = [
            'MUNICIPIUL ', 'MUN. ', 'MUN ', 'ORASUL ', 'ORAS ',
            'COMUNA ', 'COM. ', 'COM ', 'SATUL ', 'SAT ', 'SECTOR ',
        ]
        for prefix in prefixes:
            if upper_result.startswith(prefix):
                upper_result = upper_result[len(prefix):].strip()
                break
        return upper_result

    judet_norm = normalize_text(judet)
    is_bucuresti = 'BUCUREST' in judet_norm or 'BUCUREST' in localitate.upper()
    localitate_norm = normalize_text(localitate, is_bucuresti=is_bucuresti)

    try:
        locality_match = await app_db.localities.find_one({
            "judet_normalized": judet_norm,
            "localitate_normalized": localitate_norm,
        })
        if locality_match:
            return locality_match.get('primary_postal_code')
    except Exception:
        pass
    return None


async def _find_caen_description(caen_code: str) -> dict:
    """Find CAEN code description from caen_codes collection"""
    if not caen_code:
        return None

    caen_normalized = str(caen_code).strip().replace(' ', '')[:4]

    companies_db = get_companies_db()
    if companies_db is not None:
        try:
            caen_record = await companies_db.caen_codes.find_one(
                {"cod": caen_normalized},
                {"_id": 0, "denumire": 1, "sectiune": 1, "sectiune_denumire": 1},
            )
            if caen_record:
                return caen_record
        except Exception:
            pass

    app_db = get_app_db()
    if app_db is not None:
        try:
            caen_record = await app_db.caen_codes.find_one(
                {"cod": caen_normalized},
                {"_id": 0, "denumire": 1, "sectiune": 1, "sectiune_denumire": 1},
            )
            return caen_record
        except Exception:
            pass
    return None


async def _enrich_profile(profile: dict) -> dict:
    """Add postal code and CAEN description to a company profile"""
    app_db = get_app_db()
    if app_db is not None and profile.get('judet') and profile.get('localitate'):
        postal_code = await _find_postal_code(app_db, profile['judet'], profile['localitate'])
        if postal_code:
            profile['cod_postal'] = postal_code

    if profile.get('anaf_cod_caen'):
        caen_info = await _find_caen_description(profile['anaf_cod_caen'])
        if caen_info:
            profile['caen_denumire'] = caen_info.get('denumire')
            profile['caen_sectiune'] = caen_info.get('sectiune')
            profile['caen_sectiune_denumire'] = caen_info.get('sectiune_denumire')
    return profile


@router.get("/company/cui/{cui}")
async def get_company_by_cui(cui: str, current_user=Depends(get_current_user_optional)):
    """Get company by CUI"""
    db = get_companies_db()

    normalized_cui = normalize_cui(cui)
    result = await db.firme.find_one({"cui": normalized_cui})
    if not result and normalized_cui.isdigit():
        result = await db.firme.find_one({"cui": int(normalized_cui)})

    if not result:
        raise HTTPException(status_code=404, detail="Company not found")

    tier = current_user["tier"] if current_user else "public"
    profile = compute_company_profile(result, tier=tier)
    profile = await _enrich_profile(profile)
    return serialize_doc(profile)


@router.get("/company/slug/{slug}")
async def get_company_by_slug(slug: str, current_user=Depends(get_current_user_optional)):
    """Get company by slug"""
    db = get_companies_db()

    parts = slug.rsplit("-", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid slug format")

    cui = parts[1]
    normalized_cui = normalize_cui(cui)

    result = await db.firme.find_one({"cui": normalized_cui})
    if not result and normalized_cui.isdigit():
        result = await db.firme.find_one({"cui": int(normalized_cui)})

    if not result:
        raise HTTPException(status_code=404, detail="Company not found")

    tier = current_user["tier"] if current_user else "public"
    profile = compute_company_profile(result, tier=tier)
    profile = await _enrich_profile(profile)
    return serialize_doc(profile)


@router.get("/company/{cui}/financials")
async def get_company_financials(cui: str):
    """Get multi-year financial data for a company from real bilanturi collection"""
    db = get_companies_db()
    normalized_cui = normalize_cui(cui)
    company = await db.firme.find_one({"cui": normalized_cui})
    if not company and normalized_cui.isdigit():
        company = await db.firme.find_one({"cui": int(normalized_cui)})

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    firma_numeric_id = company.get('id')
    if not firma_numeric_id:
        return {"years": [], "data": [], "note": "No financial data available"}

    bilanturi_cursor = db.bilanturi.find({"firma_id": firma_numeric_id}).sort("an", 1)
    bilanturi = await bilanturi_cursor.to_list(length=100)

    if not bilanturi:
        return {"years": [], "data": [], "note": "No bilanturi found"}

    data = []
    years = []

    for bilant in bilanturi:
        an = bilant.get('an')
        if not an or str(an).startswith('WEB_'):
            continue
        try:
            year_int = int(an) if isinstance(an, str) else an
        except (ValueError, TypeError):
            continue

        years.append(year_int)
        data.append({
            'year': year_int,
            'active_imobilizate': bilant.get('active_imobilizate'),
            'active_circulante': bilant.get('active_circulante'),
            'creante': bilant.get('creante'),
            'casa_conturi_banci': bilant.get('casa_conturi_banci'),
            'datorii': bilant.get('datorii'),
            'capitaluri_proprii': bilant.get('capitaluri_proprii'),
            'capital_subscris': bilant.get('capital_subscris'),
            'cifra_afaceri': bilant.get('cifra_afaceri') or bilant.get('venituri_totale'),
            'profit_net': bilant.get('profit_net'),
            'numar_angajati': bilant.get('numar_angajati'),
            'venituri_totale': bilant.get('venituri_totale'),
            'cheltuieli_totale': bilant.get('cheltuieli_totale'),
        })

    return {
        "years": years,
        "data": data,
        "source": "real",
        "note": "Real financial data from Ministerul Finanțelor bilanțuri",
    }
