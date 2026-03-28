"""
Financial Analysis Routes - Indicatori financiari pentru contabili
Calculează și returnează indicatori financiari detaliate pentru firme
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from auth import get_current_user
from database import get_local_db, get_app_db
import logging
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/financial", tags=["financial"])


# === Helper Functions ===

def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """Safe division to avoid division by zero"""
    if denominator is None or denominator == 0:
        return default
    if numerator is None:
        return default
    return numerator / denominator


def format_currency(value: float) -> str:
    """Format value as Romanian currency"""
    if value is None:
        return "N/A"
    return f"{value:,.0f} RON".replace(",", ".")


def format_percent(value: float) -> str:
    """Format value as percentage"""
    if value is None:
        return "N/A"
    return f"{value:.2f}%"


def get_rating(value: float, thresholds: Dict[str, float], reverse: bool = False) -> str:
    """
    Get a rating based on value and thresholds
    thresholds: {'excellent': 20, 'good': 10, 'average': 5, 'poor': 0}
    """
    if value is None:
        return "N/A"
    
    if reverse:
        # Lower is better (e.g., debt ratio)
        if value <= thresholds.get('excellent', 0):
            return "Excelent"
        elif value <= thresholds.get('good', 0):
            return "Bun"
        elif value <= thresholds.get('average', 0):
            return "Mediu"
        else:
            return "Slab"
    else:
        # Higher is better (e.g., profit margin)
        if value >= thresholds.get('excellent', 100):
            return "Excelent"
        elif value >= thresholds.get('good', 50):
            return "Bun"
        elif value >= thresholds.get('average', 20):
            return "Mediu"
        else:
            return "Slab"


def calculate_financial_indicators(firma: Dict, bilanturi: List[Dict] = None) -> Dict[str, Any]:
    """
    Calculate all financial indicators for a company
    """
    if not firma:
        return {}
    
    # Extract financial data from firma
    cifra_afaceri = firma.get('mf_cifra_afaceri') or firma.get('cifra_afaceri') or 0
    venituri_totale = firma.get('mf_venituri_totale') or firma.get('venituri_totale') or cifra_afaceri
    cheltuieli_totale = firma.get('mf_cheltuieli_totale') or 0
    profit_brut = firma.get('mf_profit_brut') or 0
    profit_net = firma.get('mf_profit_net') or firma.get('profit') or 0
    active_circulante = firma.get('mf_active_circulante') or 0
    active_imobilizate = firma.get('mf_active_imobilizate') or 0
    capitaluri_proprii = firma.get('mf_capitaluri_proprii') or 0
    datorii = firma.get('mf_datorii') or 0
    numar_angajati = firma.get('mf_numar_angajati') or firma.get('numar_angajati') or 0
    an_bilant = firma.get('mf_an_bilant') or datetime.now().year
    
    # Calculate totals
    total_active = active_circulante + active_imobilizate
    
    # === PROFITABILITY INDICATORS ===
    marja_profit_brut = safe_divide(profit_brut, cifra_afaceri) * 100 if cifra_afaceri > 0 else None
    marja_profit_net = safe_divide(profit_net, cifra_afaceri) * 100 if cifra_afaceri > 0 else None
    roa = safe_divide(profit_net, total_active) * 100 if total_active > 0 else None
    roe = safe_divide(profit_net, capitaluri_proprii) * 100 if capitaluri_proprii > 0 else None
    rata_rentabilitate_economica = safe_divide(profit_brut, total_active) * 100 if total_active > 0 else None
    
    # === LIQUIDITY INDICATORS ===
    # Assuming datorii = datorii curente for simplicity (usually 70-80% of total)
    datorii_curente = datorii * 0.75  # Estimate
    lichiditate_curenta = safe_divide(active_circulante, datorii_curente) if datorii_curente > 0 else None
    
    # Get cash from bilanturi if available
    casa_banci = 0
    creante = 0
    if bilanturi and len(bilanturi) > 0:
        latest_bilant = bilanturi[0]  # Assuming sorted by year desc
        casa_banci = latest_bilant.get('casa_conturi_banci', 0) or 0
        creante = latest_bilant.get('creante', 0) or 0
    
    lichiditate_imediata = safe_divide(casa_banci, datorii_curente) if datorii_curente > 0 else None
    lichiditate_rapida = safe_divide(active_circulante - creante, datorii_curente) if datorii_curente > 0 else None
    
    # === SOLVENCY INDICATORS ===
    rata_indatorarii = safe_divide(datorii, total_active) * 100 if total_active > 0 else None
    autonomie_financiara = safe_divide(capitaluri_proprii, total_active) * 100 if total_active > 0 else None
    levier_financiar = safe_divide(datorii, capitaluri_proprii) if capitaluri_proprii > 0 else None
    solvabilitate_generala = safe_divide(total_active, datorii) if datorii > 0 else None
    
    # === EFFICIENCY INDICATORS ===
    productivitate_munca = safe_divide(cifra_afaceri, numar_angajati) if numar_angajati > 0 else None
    profit_per_angajat = safe_divide(profit_net, numar_angajati) if numar_angajati > 0 else None
    rata_cheltuieli = safe_divide(cheltuieli_totale, venituri_totale) * 100 if venituri_totale > 0 else None
    eficienta_activelor = safe_divide(cifra_afaceri, total_active) if total_active > 0 else None
    
    # === GROWTH INDICATORS (if we have historical data) ===
    growth_indicators = {}
    if bilanturi and len(bilanturi) >= 2:
        # Sort by year descending
        sorted_bilanturi = sorted(bilanturi, key=lambda x: x.get('an', '0'), reverse=True)
        if len(sorted_bilanturi) >= 2:
            current = sorted_bilanturi[0]
            previous = sorted_bilanturi[1]
            
            current_active = (current.get('active_circulante', 0) or 0) + (current.get('active_imobilizate', 0) or 0)
            previous_active = (previous.get('active_circulante', 0) or 0) + (previous.get('active_imobilizate', 0) or 0)
            
            if previous_active > 0:
                growth_indicators['crestere_active'] = ((current_active - previous_active) / previous_active) * 100
            
            current_capital = current.get('capitaluri_proprii', 0) or 0
            previous_capital = previous.get('capitaluri_proprii', 0) or 0
            if previous_capital > 0 and previous_capital != 0:
                growth_indicators['crestere_capitaluri'] = ((current_capital - previous_capital) / abs(previous_capital)) * 100
    
    # === HEALTH SCORE (0-100) ===
    health_score = 50  # Base score
    
    # Profitability contribution (+/- 20 points)
    if marja_profit_net is not None:
        if marja_profit_net > 15:
            health_score += 20
        elif marja_profit_net > 5:
            health_score += 10
        elif marja_profit_net < 0:
            health_score -= 15
    
    # Liquidity contribution (+/- 15 points)
    if lichiditate_curenta is not None:
        if lichiditate_curenta > 2:
            health_score += 15
        elif lichiditate_curenta > 1:
            health_score += 8
        elif lichiditate_curenta < 0.5:
            health_score -= 15
    
    # Solvency contribution (+/- 15 points)
    if rata_indatorarii is not None:
        if rata_indatorarii < 30:
            health_score += 15
        elif rata_indatorarii < 60:
            health_score += 5
        elif rata_indatorarii > 80:
            health_score -= 15
    
    health_score = max(0, min(100, health_score))
    
    # Determine health status
    if health_score >= 80:
        health_status = "Excelentă"
        health_color = "green"
    elif health_score >= 60:
        health_status = "Bună"
        health_color = "blue"
    elif health_score >= 40:
        health_status = "Medie"
        health_color = "yellow"
    else:
        health_status = "Slabă"
        health_color = "red"
    
    return {
        "company_info": {
            "denumire": firma.get('denumire') or firma.get('mf_denumire'),
            "cui": firma.get('cui'),
            "an_bilant": an_bilant,
            "numar_angajati": numar_angajati,
            "caen": firma.get('anaf_cod_caen') or firma.get('caen'),
        },
        "raw_data": {
            "cifra_afaceri": cifra_afaceri,
            "venituri_totale": venituri_totale,
            "cheltuieli_totale": cheltuieli_totale,
            "profit_brut": profit_brut,
            "profit_net": profit_net,
            "active_circulante": active_circulante,
            "active_imobilizate": active_imobilizate,
            "total_active": total_active,
            "capitaluri_proprii": capitaluri_proprii,
            "datorii": datorii,
            "casa_banci": casa_banci,
            "creante": creante,
        },
        "profitability": {
            "marja_profit_brut": {
                "value": marja_profit_brut,
                "formatted": format_percent(marja_profit_brut),
                "description": "Profit brut / Cifra de afaceri × 100",
                "rating": get_rating(marja_profit_brut, {'excellent': 25, 'good': 15, 'average': 5}),
                "interpretation": "Măsoară eficiența operațională de bază"
            },
            "marja_profit_net": {
                "value": marja_profit_net,
                "formatted": format_percent(marja_profit_net),
                "description": "Profit net / Cifra de afaceri × 100",
                "rating": get_rating(marja_profit_net, {'excellent': 15, 'good': 8, 'average': 3}),
                "interpretation": "Profitul final după toate cheltuielile"
            },
            "roa": {
                "value": roa,
                "formatted": format_percent(roa),
                "description": "Return on Assets - Profit net / Total active × 100",
                "rating": get_rating(roa, {'excellent': 15, 'good': 8, 'average': 3}),
                "interpretation": "Eficiența utilizării activelor pentru generarea profitului"
            },
            "roe": {
                "value": roe,
                "formatted": format_percent(roe),
                "description": "Return on Equity - Profit net / Capitaluri proprii × 100",
                "rating": get_rating(roe, {'excellent': 20, 'good': 12, 'average': 5}),
                "interpretation": "Randamentul investiției acționarilor"
            },
            "rata_rentabilitate_economica": {
                "value": rata_rentabilitate_economica,
                "formatted": format_percent(rata_rentabilitate_economica),
                "description": "Profit brut / Total active × 100",
                "rating": get_rating(rata_rentabilitate_economica, {'excellent': 20, 'good': 10, 'average': 5}),
                "interpretation": "Capacitatea de a genera profit din active"
            }
        },
        "liquidity": {
            "lichiditate_curenta": {
                "value": lichiditate_curenta,
                "formatted": f"{lichiditate_curenta:.2f}" if lichiditate_curenta else "N/A",
                "description": "Active circulante / Datorii curente",
                "rating": get_rating(lichiditate_curenta, {'excellent': 2.5, 'good': 1.5, 'average': 1.0}) if lichiditate_curenta else "N/A",
                "interpretation": "Capacitatea de a acoperi datoriile pe termen scurt. Ideal > 1.5"
            },
            "lichiditate_rapida": {
                "value": lichiditate_rapida,
                "formatted": f"{lichiditate_rapida:.2f}" if lichiditate_rapida else "N/A",
                "description": "(Active circulante - Stocuri) / Datorii curente",
                "rating": get_rating(lichiditate_rapida, {'excellent': 1.5, 'good': 1.0, 'average': 0.7}) if lichiditate_rapida else "N/A",
                "interpretation": "Test acid - lichiditate fără stocuri"
            },
            "lichiditate_imediata": {
                "value": lichiditate_imediata,
                "formatted": f"{lichiditate_imediata:.2f}" if lichiditate_imediata else "N/A",
                "description": "Casa și bănci / Datorii curente",
                "rating": get_rating(lichiditate_imediata, {'excellent': 0.5, 'good': 0.3, 'average': 0.1}) if lichiditate_imediata else "N/A",
                "interpretation": "Cash disponibil pentru plăți imediate"
            }
        },
        "solvency": {
            "rata_indatorarii": {
                "value": rata_indatorarii,
                "formatted": format_percent(rata_indatorarii),
                "description": "Datorii totale / Total active × 100",
                "rating": get_rating(rata_indatorarii, {'excellent': 30, 'good': 50, 'average': 70}, reverse=True),
                "interpretation": "Gradul de finanțare prin datorii. Sub 50% = sănătos"
            },
            "autonomie_financiara": {
                "value": autonomie_financiara,
                "formatted": format_percent(autonomie_financiara),
                "description": "Capitaluri proprii / Total active × 100",
                "rating": get_rating(autonomie_financiara, {'excellent': 60, 'good': 40, 'average': 25}),
                "interpretation": "Independența față de creditori. Peste 50% = bun"
            },
            "levier_financiar": {
                "value": levier_financiar,
                "formatted": f"{levier_financiar:.2f}" if levier_financiar else "N/A",
                "description": "Datorii / Capitaluri proprii",
                "rating": get_rating(levier_financiar, {'excellent': 0.5, 'good': 1.0, 'average': 2.0}, reverse=True) if levier_financiar else "N/A",
                "interpretation": "Sub 1 = firma finanțată mai mult din capitaluri proprii"
            },
            "solvabilitate_generala": {
                "value": solvabilitate_generala,
                "formatted": f"{solvabilitate_generala:.2f}" if solvabilitate_generala else "N/A",
                "description": "Total active / Datorii totale",
                "rating": get_rating(solvabilitate_generala, {'excellent': 3, 'good': 2, 'average': 1.5}) if solvabilitate_generala else "N/A",
                "interpretation": "Capacitatea de a acoperi toate datoriile. Peste 2 = bun"
            }
        },
        "efficiency": {
            "productivitate_munca": {
                "value": productivitate_munca,
                "formatted": format_currency(productivitate_munca),
                "description": "Cifra de afaceri / Număr angajați",
                "interpretation": "Venituri generate per angajat"
            },
            "profit_per_angajat": {
                "value": profit_per_angajat,
                "formatted": format_currency(profit_per_angajat),
                "description": "Profit net / Număr angajați",
                "interpretation": "Contribuția fiecărui angajat la profit"
            },
            "rata_cheltuieli": {
                "value": rata_cheltuieli,
                "formatted": format_percent(rata_cheltuieli),
                "description": "Cheltuieli totale / Venituri totale × 100",
                "rating": get_rating(rata_cheltuieli, {'excellent': 80, 'good': 90, 'average': 95}, reverse=True),
                "interpretation": "Cât din venituri se duce pe cheltuieli. Sub 90% = bun"
            },
            "eficienta_activelor": {
                "value": eficienta_activelor,
                "formatted": f"{eficienta_activelor:.2f}" if eficienta_activelor else "N/A",
                "description": "Cifra de afaceri / Total active",
                "interpretation": "De câte ori activele generează venituri anual"
            }
        },
        "growth": growth_indicators,
        "health_score": {
            "score": health_score,
            "status": health_status,
            "color": health_color,
            "interpretation": f"Scor de sănătate financiară: {health_score}/100 - {health_status}"
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


# === API ENDPOINTS ===

@router.get("/indicators/{cui}")
async def get_financial_indicators(cui: str):
    """
    Get all financial indicators for a company by CUI
    Public endpoint - basic indicators
    """
    local_db = get_local_db()
    
    # Find company
    firma = await local_db.firme.find_one({"cui": cui})
    if not firma:
        # Try as integer
        try:
            firma = await local_db.firme.find_one({"cui": int(cui)})
        except:
            pass
    
    if not firma:
        raise HTTPException(status_code=404, detail="Firma nu a fost găsită")
    
    # Get bilanturi for historical data
    firma_id = firma.get('id')
    bilanturi = []
    if firma_id:
        cursor = local_db.bilanturi.find({"firma_id": firma_id}).sort("an", -1)
        bilanturi = await cursor.to_list(length=10)
    
    indicators = calculate_financial_indicators(firma, bilanturi)
    
    return indicators


@router.get("/indicators/{cui}/pdf")
async def get_financial_report_pdf(cui: str):
    """
    Generate PDF financial report for a company
    """
    local_db = get_local_db()
    
    # Find company
    firma = await local_db.firme.find_one({"cui": cui})
    if not firma:
        try:
            firma = await local_db.firme.find_one({"cui": int(cui)})
        except:
            pass
    
    if not firma:
        raise HTTPException(status_code=404, detail="Firma nu a fost găsită")
    
    # Get bilanturi
    firma_id = firma.get('id')
    bilanturi = []
    if firma_id:
        cursor = local_db.bilanturi.find({"firma_id": firma_id}).sort("an", -1)
        bilanturi = await cursor.to_list(length=10)
    
    indicators = calculate_financial_indicators(firma, bilanturi)
    
    # Generate PDF using HTML template
    html_content = generate_pdf_html(indicators)
    
    # Return HTML for now (can be converted to PDF with weasyprint/puppeteer)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"inline; filename=raport_financiar_{cui}.html"
        }
    )


@router.get("/industry/{caen}")
async def get_industry_statistics(caen: str, limit: int = 100):
    """
    Get aggregated statistics for an industry (by CAEN code)
    """
    local_db = get_local_db()
    
    # Normalize CAEN to 4 digits
    caen_4 = caen[:4] if len(caen) >= 4 else caen
    
    # Aggregate statistics
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"anaf_cod_caen": {"$regex": f"^{caen_4}"}},
                    {"caen": {"$regex": f"^{caen_4}"}}
                ],
                "mf_cifra_afaceri": {"$gt": 0}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_firme": {"$sum": 1},
                "total_angajati": {"$sum": {"$ifNull": ["$mf_numar_angajati", 0]}},
                "total_cifra_afaceri": {"$sum": {"$ifNull": ["$mf_cifra_afaceri", 0]}},
                "total_profit": {"$sum": {"$ifNull": ["$mf_profit_net", 0]}},
                "avg_cifra_afaceri": {"$avg": {"$ifNull": ["$mf_cifra_afaceri", 0]}},
                "avg_profit": {"$avg": {"$ifNull": ["$mf_profit_net", 0]}},
                "avg_angajati": {"$avg": {"$ifNull": ["$mf_numar_angajati", 0]}},
                "max_cifra_afaceri": {"$max": "$mf_cifra_afaceri"},
                "min_cifra_afaceri": {"$min": "$mf_cifra_afaceri"},
                "avg_active": {"$avg": {"$add": [
                    {"$ifNull": ["$mf_active_circulante", 0]},
                    {"$ifNull": ["$mf_active_imobilizate", 0]}
                ]}},
                "avg_datorii": {"$avg": {"$ifNull": ["$mf_datorii", 0]}},
                "avg_capitaluri": {"$avg": {"$ifNull": ["$mf_capitaluri_proprii", 0]}}
            }
        }
    ]
    
    result = await local_db.firme.aggregate(pipeline).to_list(length=1)
    
    if not result:
        return {
            "caen": caen_4,
            "message": "Nu există date pentru acest cod CAEN",
            "statistics": None
        }
    
    stats = result[0]
    
    # Calculate industry averages
    avg_ca = stats.get('avg_cifra_afaceri', 0) or 0
    avg_profit = stats.get('avg_profit', 0) or 0
    avg_active = stats.get('avg_active', 0) or 0
    
    return {
        "caen": caen_4,
        "statistics": {
            "total_firme": stats.get('total_firme', 0),
            "total_angajati": stats.get('total_angajati', 0),
            "total_cifra_afaceri": stats.get('total_cifra_afaceri', 0),
            "total_profit": stats.get('total_profit', 0),
            "medii": {
                "cifra_afaceri": avg_ca,
                "profit_net": avg_profit,
                "numar_angajati": stats.get('avg_angajati', 0),
                "total_active": avg_active,
                "datorii": stats.get('avg_datorii', 0),
                "capitaluri_proprii": stats.get('avg_capitaluri', 0)
            },
            "indicatori_industrie": {
                "marja_profit_medie": safe_divide(avg_profit, avg_ca) * 100 if avg_ca > 0 else 0,
                "productivitate_medie": safe_divide(avg_ca, stats.get('avg_angajati', 1)) if stats.get('avg_angajati', 0) > 0 else 0
            },
            "range": {
                "max_cifra_afaceri": stats.get('max_cifra_afaceri', 0),
                "min_cifra_afaceri": stats.get('min_cifra_afaceri', 0)
            }
        }
    }


@router.get("/compare/{cui}")
async def compare_with_industry(cui: str):
    """
    Compare a company with its industry average
    """
    local_db = get_local_db()
    
    # Get company indicators
    firma = await local_db.firme.find_one({"cui": cui})
    if not firma:
        try:
            firma = await local_db.firme.find_one({"cui": int(cui)})
        except:
            pass
    
    if not firma:
        raise HTTPException(status_code=404, detail="Firma nu a fost găsită")
    
    # Get company's CAEN
    caen = firma.get('anaf_cod_caen') or firma.get('caen') or ''
    caen_4 = str(caen)[:4] if caen else ''
    
    if not caen_4:
        return {
            "message": "Codul CAEN nu este disponibil pentru această firmă",
            "company": None,
            "industry": None
        }
    
    # Get industry statistics
    industry_stats = await get_industry_statistics(caen_4)
    
    # Get company indicators
    firma_id = firma.get('id')
    bilanturi = []
    if firma_id:
        cursor = local_db.bilanturi.find({"firma_id": firma_id}).sort("an", -1)
        bilanturi = await cursor.to_list(length=10)
    
    company_indicators = calculate_financial_indicators(firma, bilanturi)
    
    # Calculate comparison
    industry_medii = industry_stats.get('statistics', {}).get('medii', {})
    company_raw = company_indicators.get('raw_data', {})
    
    comparison = {
        "cifra_afaceri": {
            "company": company_raw.get('cifra_afaceri', 0),
            "industry_avg": industry_medii.get('cifra_afaceri', 0),
            "percentile": "N/A",  # Would need more data to calculate
            "vs_industry": "peste medie" if company_raw.get('cifra_afaceri', 0) > industry_medii.get('cifra_afaceri', 0) else "sub medie"
        },
        "profit_net": {
            "company": company_raw.get('profit_net', 0),
            "industry_avg": industry_medii.get('profit_net', 0),
            "vs_industry": "peste medie" if company_raw.get('profit_net', 0) > industry_medii.get('profit_net', 0) else "sub medie"
        },
        "numar_angajati": {
            "company": company_indicators.get('company_info', {}).get('numar_angajati', 0),
            "industry_avg": industry_medii.get('numar_angajati', 0),
        }
    }
    
    return {
        "company": company_indicators,
        "industry": industry_stats,
        "comparison": comparison,
        "caen": caen_4
    }


@router.get("/admin/dashboard")
async def get_admin_financial_dashboard(current_user = Depends(get_current_user)):
    """
    Admin dashboard with aggregated financial statistics
    """
    app_db = get_app_db()
    local_db = get_local_db()
    
    # Verify admin
    user = await app_db.users.find_one({"email": current_user["email"]})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get overall statistics
    pipeline = [
        {
            "$match": {
                "mf_cifra_afaceri": {"$gt": 0}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_firme_cu_date": {"$sum": 1},
                "total_cifra_afaceri": {"$sum": "$mf_cifra_afaceri"},
                "total_profit": {"$sum": {"$ifNull": ["$mf_profit_net", 0]}},
                "total_angajati": {"$sum": {"$ifNull": ["$mf_numar_angajati", 0]}},
                "avg_cifra_afaceri": {"$avg": "$mf_cifra_afaceri"},
                "avg_profit": {"$avg": {"$ifNull": ["$mf_profit_net", 0]}},
                "firme_profit": {"$sum": {"$cond": [{"$gt": ["$mf_profit_net", 0]}, 1, 0]}},
                "firme_pierdere": {"$sum": {"$cond": [{"$lt": ["$mf_profit_net", 0]}, 1, 0]}}
            }
        }
    ]
    
    overall = await local_db.firme.aggregate(pipeline).to_list(length=1)
    overall_stats = overall[0] if overall else {}
    
    # Get top industries by revenue
    industry_pipeline = [
        {
            "$match": {
                "mf_cifra_afaceri": {"$gt": 0},
                "anaf_cod_caen": {"$exists": True, "$ne": None}
            }
        },
        {
            "$group": {
                "_id": {"$substr": ["$anaf_cod_caen", 0, 2]},  # First 2 digits = sector
                "total_firme": {"$sum": 1},
                "total_cifra_afaceri": {"$sum": "$mf_cifra_afaceri"},
                "total_angajati": {"$sum": {"$ifNull": ["$mf_numar_angajati", 0]}},
                "avg_profit_margin": {"$avg": {
                    "$cond": [
                        {"$gt": ["$mf_cifra_afaceri", 0]},
                        {"$multiply": [{"$divide": [{"$ifNull": ["$mf_profit_net", 0]}, "$mf_cifra_afaceri"]}, 100]},
                        0
                    ]
                }}
            }
        },
        {"$sort": {"total_cifra_afaceri": -1}},
        {"$limit": 10}
    ]
    
    top_industries = await local_db.firme.aggregate(industry_pipeline).to_list(length=10)
    
    # Get top counties
    county_pipeline = [
        {
            "$match": {
                "mf_cifra_afaceri": {"$gt": 0},
                "judet": {"$exists": True, "$ne": None}
            }
        },
        {
            "$group": {
                "_id": "$judet",
                "total_firme": {"$sum": 1},
                "total_cifra_afaceri": {"$sum": "$mf_cifra_afaceri"},
                "avg_cifra_afaceri": {"$avg": "$mf_cifra_afaceri"}
            }
        },
        {"$sort": {"total_cifra_afaceri": -1}},
        {"$limit": 10}
    ]
    
    top_counties = await local_db.firme.aggregate(county_pipeline).to_list(length=10)
    
    return {
        "overall": {
            "total_firme_cu_date_financiare": overall_stats.get('total_firme_cu_date', 0),
            "total_cifra_afaceri": overall_stats.get('total_cifra_afaceri', 0),
            "total_profit": overall_stats.get('total_profit', 0),
            "total_angajati": overall_stats.get('total_angajati', 0),
            "media_cifra_afaceri": overall_stats.get('avg_cifra_afaceri', 0),
            "media_profit": overall_stats.get('avg_profit', 0),
            "firme_profitabile": overall_stats.get('firme_profit', 0),
            "firme_in_pierdere": overall_stats.get('firme_pierdere', 0),
            "rata_profitabilitate": safe_divide(overall_stats.get('firme_profit', 0), overall_stats.get('total_firme_cu_date', 1)) * 100
        },
        "top_industries": [
            {
                "sector_caen": ind['_id'],
                "total_firme": ind['total_firme'],
                "total_cifra_afaceri": ind['total_cifra_afaceri'],
                "total_angajati": ind['total_angajati'],
                "marja_profit_medie": ind['avg_profit_margin']
            }
            for ind in top_industries
        ],
        "top_counties": [
            {
                "judet": county['_id'],
                "total_firme": county['total_firme'],
                "total_cifra_afaceri": county['total_cifra_afaceri'],
                "media_cifra_afaceri": county['avg_cifra_afaceri']
            }
            for county in top_counties
        ],
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/admin/recalculate")
async def recalculate_statistics(current_user = Depends(get_current_user)):
    """
    Recalculate and cache all financial statistics
    This should be called after a database sync
    """
    app_db = get_app_db()
    local_db = get_local_db()
    
    # Verify admin
    user = await app_db.users.find_one({"email": current_user["email"]})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info(f"Starting financial statistics recalculation by {user.get('email')}")
    
    try:
        # Count total companies
        total_firme = await local_db.firme.count_documents({})
        firme_cu_date = await local_db.firme.count_documents({"mf_cifra_afaceri": {"$gt": 0}})
        
        # Overall statistics
        overall_pipeline = [
            {"$match": {"mf_cifra_afaceri": {"$gt": 0}}},
            {
                "$group": {
                    "_id": None,
                    "total_firme_cu_date": {"$sum": 1},
                    "total_cifra_afaceri": {"$sum": "$mf_cifra_afaceri"},
                    "total_profit": {"$sum": {"$ifNull": ["$mf_profit_net", 0]}},
                    "total_angajati": {"$sum": {"$ifNull": ["$mf_numar_angajati", 0]}},
                    "avg_cifra_afaceri": {"$avg": "$mf_cifra_afaceri"},
                    "avg_profit": {"$avg": {"$ifNull": ["$mf_profit_net", 0]}},
                    "firme_profit": {"$sum": {"$cond": [{"$gt": ["$mf_profit_net", 0]}, 1, 0]}},
                    "firme_pierdere": {"$sum": {"$cond": [{"$lt": ["$mf_profit_net", 0]}, 1, 0]}},
                    "total_active": {"$sum": {"$add": [
                        {"$ifNull": ["$mf_active_circulante", 0]},
                        {"$ifNull": ["$mf_active_imobilizate", 0]}
                    ]}},
                    "total_datorii": {"$sum": {"$ifNull": ["$mf_datorii", 0]}},
                    "total_capitaluri": {"$sum": {"$ifNull": ["$mf_capitaluri_proprii", 0]}}
                }
            }
        ]
        
        overall_result = await local_db.firme.aggregate(overall_pipeline).to_list(length=1)
        overall_stats = overall_result[0] if overall_result else {}
        
        # Industry statistics (top 20)
        industry_pipeline = [
            {
                "$match": {
                    "mf_cifra_afaceri": {"$gt": 0},
                    "$or": [
                        {"anaf_cod_caen": {"$exists": True, "$ne": None}},
                        {"caen": {"$exists": True, "$ne": None}}
                    ]
                }
            },
            {
                "$addFields": {
                    "caen_sector": {
                        "$substr": [
                            {"$ifNull": [{"$toString": "$anaf_cod_caen"}, {"$toString": "$caen"}]},
                            0, 2
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$caen_sector",
                    "total_firme": {"$sum": 1},
                    "total_cifra_afaceri": {"$sum": "$mf_cifra_afaceri"},
                    "total_profit": {"$sum": {"$ifNull": ["$mf_profit_net", 0]}},
                    "total_angajati": {"$sum": {"$ifNull": ["$mf_numar_angajati", 0]}},
                    "avg_cifra_afaceri": {"$avg": "$mf_cifra_afaceri"},
                    "avg_profit": {"$avg": {"$ifNull": ["$mf_profit_net", 0]}},
                    "avg_angajati": {"$avg": {"$ifNull": ["$mf_numar_angajati", 0]}}
                }
            },
            {"$sort": {"total_cifra_afaceri": -1}},
            {"$limit": 20}
        ]
        
        industry_stats = await local_db.firme.aggregate(industry_pipeline).to_list(length=20)
        
        # County statistics (all)
        county_pipeline = [
            {
                "$match": {
                    "mf_cifra_afaceri": {"$gt": 0},
                    "judet": {"$exists": True, "$ne": None, "$ne": ""}
                }
            },
            {
                "$group": {
                    "_id": "$judet",
                    "total_firme": {"$sum": 1},
                    "total_cifra_afaceri": {"$sum": "$mf_cifra_afaceri"},
                    "total_profit": {"$sum": {"$ifNull": ["$mf_profit_net", 0]}},
                    "total_angajati": {"$sum": {"$ifNull": ["$mf_numar_angajati", 0]}},
                    "avg_cifra_afaceri": {"$avg": "$mf_cifra_afaceri"}
                }
            },
            {"$sort": {"total_cifra_afaceri": -1}}
        ]
        
        county_stats = await local_db.firme.aggregate(county_pipeline).to_list(length=50)
        
        # Calculate aggregate indicators
        total_ca = overall_stats.get('total_cifra_afaceri', 0) or 0
        total_profit = overall_stats.get('total_profit', 0) or 0
        total_active = overall_stats.get('total_active', 0) or 0
        total_datorii = overall_stats.get('total_datorii', 0) or 0
        total_capitaluri = overall_stats.get('total_capitaluri', 0) or 0
        
        aggregate_indicators = {
            "marja_profit_nationala": safe_divide(total_profit, total_ca) * 100,
            "rata_indatorare_nationala": safe_divide(total_datorii, total_active) * 100,
            "roa_national": safe_divide(total_profit, total_active) * 100,
            "roe_national": safe_divide(total_profit, total_capitaluri) * 100 if total_capitaluri > 0 else 0
        }
        
        # Save to cache collection
        cache_doc = {
            "type": "financial_dashboard",
            "total_firme": total_firme,
            "firme_cu_date_financiare": firme_cu_date,
            "overall": {
                "total_firme_cu_date_financiare": overall_stats.get('total_firme_cu_date', 0),
                "total_cifra_afaceri": total_ca,
                "total_profit": total_profit,
                "total_angajati": overall_stats.get('total_angajati', 0),
                "total_active": total_active,
                "total_datorii": total_datorii,
                "total_capitaluri": total_capitaluri,
                "media_cifra_afaceri": overall_stats.get('avg_cifra_afaceri', 0),
                "media_profit": overall_stats.get('avg_profit', 0),
                "firme_profitabile": overall_stats.get('firme_profit', 0),
                "firme_in_pierdere": overall_stats.get('firme_pierdere', 0),
                "rata_profitabilitate": safe_divide(overall_stats.get('firme_profit', 0), overall_stats.get('total_firme_cu_date', 1)) * 100
            },
            "aggregate_indicators": aggregate_indicators,
            "top_industries": [
                {
                    "sector_caen": ind['_id'],
                    "total_firme": ind['total_firme'],
                    "total_cifra_afaceri": ind['total_cifra_afaceri'],
                    "total_profit": ind['total_profit'],
                    "total_angajati": ind['total_angajati'],
                    "avg_cifra_afaceri": ind['avg_cifra_afaceri'],
                    "marja_profit_medie": safe_divide(ind['total_profit'], ind['total_cifra_afaceri']) * 100
                }
                for ind in industry_stats
            ],
            "counties": [
                {
                    "judet": county['_id'],
                    "total_firme": county['total_firme'],
                    "total_cifra_afaceri": county['total_cifra_afaceri'],
                    "total_profit": county['total_profit'],
                    "total_angajati": county['total_angajati'],
                    "media_cifra_afaceri": county['avg_cifra_afaceri']
                }
                for county in county_stats
            ],
            "calculated_at": datetime.now(timezone.utc),
            "calculated_by": user.get('email')
        }
        
        # Upsert the cache document
        await app_db.financial_cache.update_one(
            {"type": "financial_dashboard"},
            {"$set": cache_doc},
            upsert=True
        )
        
        logger.info(f"Financial statistics recalculated: {firme_cu_date} companies with data")
        
        return {
            "status": "success",
            "message": f"Statistici recalculate cu succes pentru {firme_cu_date:,} firme cu date financiare",
            "summary": {
                "total_firme": total_firme,
                "firme_cu_date_financiare": firme_cu_date,
                "total_cifra_afaceri": total_ca,
                "total_profit": total_profit,
                "judete_analizate": len(county_stats),
                "industrii_analizate": len(industry_stats)
            },
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recalculating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Eroare la recalculare: {str(e)}")


@router.get("/admin/dashboard/cached")
async def get_cached_dashboard(current_user = Depends(get_current_user)):
    """
    Get cached financial dashboard (faster than live calculation)
    """
    app_db = get_app_db()
    
    # Verify admin
    user = await app_db.users.find_one({"email": current_user["email"]})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get cached data
    cache = await app_db.financial_cache.find_one({"type": "financial_dashboard"})
    
    if not cache:
        return {
            "cached": False,
            "message": "Nu există date în cache. Apasă 'Recalculează' pentru a genera statistici.",
            "data": None
        }
    
    cache.pop('_id', None)
    
    return {
        "cached": True,
        "calculated_at": cache.get('calculated_at'),
        "calculated_by": cache.get('calculated_by'),
        "data": cache
    }


@router.get("/admin/db-info")
async def get_database_info(current_user = Depends(get_current_user)):
    """
    Get information about the current database state
    """
    app_db = get_app_db()
    local_db = get_local_db()
    
    # Verify admin
    user = await app_db.users.find_one({"email": current_user["email"]})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get collection stats
    total_firme = await local_db.firme.count_documents({})
    firme_cu_mf = await local_db.firme.count_documents({"mf_cifra_afaceri": {"$exists": True}})
    firme_cu_anaf = await local_db.firme.count_documents({"anaf_denumire": {"$exists": True}})
    total_bilanturi = await local_db.bilanturi.count_documents({})
    
    # Get latest sync info
    latest_firma = await local_db.firme.find_one(
        {"mf_last_sync": {"$exists": True}},
        sort=[("mf_last_sync", -1)]
    )
    
    # Get cache info
    cache = await app_db.financial_cache.find_one({"type": "financial_dashboard"})
    
    return {
        "database": {
            "total_firme": total_firme,
            "firme_cu_date_mf": firme_cu_mf,
            "firme_cu_date_anaf": firme_cu_anaf,
            "total_bilanturi": total_bilanturi
        },
        "last_mf_sync": latest_firma.get('mf_last_sync') if latest_firma else None,
        "cache": {
            "exists": cache is not None,
            "calculated_at": cache.get('calculated_at') if cache else None,
            "firme_in_cache": cache.get('firme_cu_date_financiare') if cache else 0
        }
    }


def generate_pdf_html(indicators: Dict) -> str:
    """Generate HTML template for PDF report"""
    company = indicators.get('company_info', {})
    raw = indicators.get('raw_data', {})
    prof = indicators.get('profitability', {})
    liq = indicators.get('liquidity', {})
    solv = indicators.get('solvency', {})
    eff = indicators.get('efficiency', {})
    health = indicators.get('health_score', {})
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Raport Financiar - {company.get('denumire', 'N/A')}</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #333; }}
            h1 {{ color: #1a365d; border-bottom: 3px solid #3182ce; padding-bottom: 10px; }}
            h2 {{ color: #2c5282; margin-top: 30px; border-left: 4px solid #3182ce; padding-left: 15px; }}
            .header {{ background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
            .header h1 {{ color: white; border: none; margin: 0; }}
            .header p {{ margin: 5px 0; opacity: 0.9; }}
            .health-score {{ 
                display: inline-block; 
                padding: 15px 30px; 
                border-radius: 50px; 
                font-size: 24px; 
                font-weight: bold;
                margin: 20px 0;
            }}
            .health-green {{ background: #c6f6d5; color: #22543d; }}
            .health-blue {{ background: #bee3f8; color: #2a4365; }}
            .health-yellow {{ background: #fefcbf; color: #744210; }}
            .health-red {{ background: #fed7d7; color: #742a2a; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
            th {{ background: #edf2f7; font-weight: 600; }}
            .value {{ font-weight: bold; color: #2d3748; }}
            .rating-Excelent {{ color: #22543d; background: #c6f6d5; padding: 3px 10px; border-radius: 15px; }}
            .rating-Bun {{ color: #2a4365; background: #bee3f8; padding: 3px 10px; border-radius: 15px; }}
            .rating-Mediu {{ color: #744210; background: #fefcbf; padding: 3px 10px; border-radius: 15px; }}
            .rating-Slab {{ color: #742a2a; background: #fed7d7; padding: 3px 10px; border-radius: 15px; }}
            .section {{ background: #f7fafc; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #718096; font-size: 12px; }}
            .interpretation {{ font-size: 12px; color: #718096; font-style: italic; }}
            @media print {{
                body {{ margin: 20px; }}
                .section {{ break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Raport Analiză Financiară</h1>
            <p><strong>{company.get('denumire', 'N/A')}</strong></p>
            <p>CUI: {company.get('cui', 'N/A')} | An bilanț: {company.get('an_bilant', 'N/A')} | Angajați: {company.get('numar_angajati', 'N/A')}</p>
        </div>
        
        <div class="section" style="text-align: center;">
            <h2 style="border: none; text-align: center;">Scor Sănătate Financiară</h2>
            <div class="health-score health-{health.get('color', 'blue')}">
                {health.get('score', 0)}/100 - {health.get('status', 'N/A')}
            </div>
        </div>
        
        <h2>Date Financiare de Bază</h2>
        <table>
            <tr><th>Indicator</th><th>Valoare</th></tr>
            <tr><td>Cifra de afaceri</td><td class="value">{format_currency(raw.get('cifra_afaceri'))}</td></tr>
            <tr><td>Venituri totale</td><td class="value">{format_currency(raw.get('venituri_totale'))}</td></tr>
            <tr><td>Cheltuieli totale</td><td class="value">{format_currency(raw.get('cheltuieli_totale'))}</td></tr>
            <tr><td>Profit brut</td><td class="value">{format_currency(raw.get('profit_brut'))}</td></tr>
            <tr><td>Profit net</td><td class="value">{format_currency(raw.get('profit_net'))}</td></tr>
            <tr><td>Total active</td><td class="value">{format_currency(raw.get('total_active'))}</td></tr>
            <tr><td>Capitaluri proprii</td><td class="value">{format_currency(raw.get('capitaluri_proprii'))}</td></tr>
            <tr><td>Datorii</td><td class="value">{format_currency(raw.get('datorii'))}</td></tr>
        </table>
        
        <h2>Indicatori de Profitabilitate</h2>
        <div class="section">
            <table>
                <tr><th>Indicator</th><th>Valoare</th><th>Rating</th><th>Interpretare</th></tr>
    """
    
    for key, val in prof.items():
        rating_class = f"rating-{val.get('rating', 'N/A')}"
        html += f"""
                <tr>
                    <td><strong>{key.replace('_', ' ').title()}</strong><br><span class="interpretation">{val.get('description', '')}</span></td>
                    <td class="value">{val.get('formatted', 'N/A')}</td>
                    <td><span class="{rating_class}">{val.get('rating', 'N/A')}</span></td>
                    <td class="interpretation">{val.get('interpretation', '')}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <h2>Indicatori de Lichiditate</h2>
        <div class="section">
            <table>
                <tr><th>Indicator</th><th>Valoare</th><th>Rating</th><th>Interpretare</th></tr>
    """
    
    for key, val in liq.items():
        rating_class = f"rating-{val.get('rating', 'N/A')}"
        html += f"""
                <tr>
                    <td><strong>{key.replace('_', ' ').title()}</strong><br><span class="interpretation">{val.get('description', '')}</span></td>
                    <td class="value">{val.get('formatted', 'N/A')}</td>
                    <td><span class="{rating_class}">{val.get('rating', 'N/A')}</span></td>
                    <td class="interpretation">{val.get('interpretation', '')}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <h2>Indicatori de Solvabilitate</h2>
        <div class="section">
            <table>
                <tr><th>Indicator</th><th>Valoare</th><th>Rating</th><th>Interpretare</th></tr>
    """
    
    for key, val in solv.items():
        rating_class = f"rating-{val.get('rating', 'N/A')}"
        html += f"""
                <tr>
                    <td><strong>{key.replace('_', ' ').title()}</strong><br><span class="interpretation">{val.get('description', '')}</span></td>
                    <td class="value">{val.get('formatted', 'N/A')}</td>
                    <td><span class="{rating_class}">{val.get('rating', 'N/A')}</span></td>
                    <td class="interpretation">{val.get('interpretation', '')}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <h2>Indicatori de Eficiență</h2>
        <div class="section">
            <table>
                <tr><th>Indicator</th><th>Valoare</th><th>Interpretare</th></tr>
    """
    
    for key, val in eff.items():
        html += f"""
                <tr>
                    <td><strong>{key.replace('_', ' ').title()}</strong><br><span class="interpretation">{val.get('description', '')}</span></td>
                    <td class="value">{val.get('formatted', 'N/A')}</td>
                    <td class="interpretation">{val.get('interpretation', '')}</td>
                </tr>
        """
    
    html += f"""
            </table>
        </div>
        
        <div class="footer">
            <p>Raport generat de mFirme.ro la {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            <p>Datele sunt preluate din sursele oficiale ANAF și Ministerul Finanțelor. Acest raport are caracter informativ.</p>
        </div>
    </body>
    </html>
    """
    
    return html
