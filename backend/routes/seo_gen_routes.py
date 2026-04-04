"""
SEO Text Generation Routes
Batch AI generation of SEO descriptions for companies using Gemini Flash
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth import get_current_user
from database import get_local_db
from datetime import datetime, timezone
import asyncio
import logging
import os
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/seo-gen", tags=["admin-seo-gen"])

# ── In-memory generation state ────────────────────────────────────────────
gen_state = {
    "running": False,
    "should_stop": False,
    "processed": 0,
    "errors": 0,
    "skipped": 0,
    "total_target": 0,
    "started_at": None,
    "last_cui": None,
    "last_error": None,
    "speed_per_min": 0,
}

SEO_PROMPT_TEMPLATE = """Generează o descriere SEO în limba română pentru această firmă românească.
Descrierea trebuie să aibă între 150-200 de cuvinte, să fie informativă și optimizată pentru motoare de căutare.
Include cuvinte cheie relevante pentru domeniul de activitate.

Date firmă:
- Denumire: {denumire}
- CUI: {cui}
- Forma juridică: {forma_juridica}
- Județ: {judet}
- Localitate: {localitate}
- Cod CAEN: {caen} ({caen_desc})
- Stare ANAF: {stare}
- Cifra de afaceri: {cifra_afaceri}
- Profit net: {profit_net}
- Număr angajați: {nr_angajati}
- An bilanț: {an_bilant}

Scrie DOAR descrierea, fără titlu, fără ghilimele, fără prefixuri."""


def _format_money(val):
    if not val or val == 0:
        return "nedisponibil"
    try:
        v = int(val)
        if v >= 1_000_000:
            return f"{v / 1_000_000:.1f} mil. RON"
        if v >= 1_000:
            return f"{v / 1_000:.0f} mii RON"
        return f"{v} RON"
    except (ValueError, TypeError):
        return "nedisponibil"


def _build_prompt(company: dict, caen_desc: str = "") -> str:
    return SEO_PROMPT_TEMPLATE.format(
        denumire=company.get("denumire", "N/A"),
        cui=company.get("cui", "N/A"),
        forma_juridica=company.get("forma_juridica", "N/A"),
        judet=company.get("judet", "N/A"),
        localitate=company.get("localitate", "N/A"),
        caen=company.get("anaf_cod_caen", "N/A"),
        caen_desc=caen_desc or "necunoscut",
        stare=company.get("anaf_stare", "N/A"),
        cifra_afaceri=_format_money(company.get("mf_cifra_afaceri")),
        profit_net=_format_money(company.get("mf_profit_net")),
        nr_angajati=company.get("mf_numar_angajati", "nedisponibil"),
        an_bilant=company.get("mf_an_bilant", "N/A"),
    )


async def _generate_one(api_key: str, company: dict, caen_desc: str = "") -> str:
    """Generate SEO text for one company using Gemini Flash."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    prompt = _build_prompt(company, caen_desc)
    session_id = f"seo-{company.get('cui', 'x')}-{uuid.uuid4().hex[:6]}"

    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="Ești un expert SEO specializat pe firme românești. Generezi descrieri concise, informative și optimizate pentru Google.",
    ).with_model("gemini", "gemini-2.5-flash")

    msg = UserMessage(text=prompt)
    response = await chat.send_message(msg)
    return response.strip()


async def _run_batch_generation(concurrency: int, limit: int):
    """Background task — batch generate SEO descriptions."""
    global gen_state
    gen_state["running"] = True
    gen_state["should_stop"] = False
    gen_state["processed"] = 0
    gen_state["errors"] = 0
    gen_state["skipped"] = 0
    gen_state["started_at"] = datetime.now(timezone.utc).isoformat()
    gen_state["last_error"] = None

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        gen_state["running"] = False
        gen_state["last_error"] = "GEMINI_API_KEY not set in .env"
        return

    db = get_local_db()

    # Count target firms (active, no SEO text yet)
    query = {"anaf_inactiv": {"$ne": True}, "seo_description": {"$exists": False}}
    gen_state["total_target"] = await db.firme.count_documents(query)

    if limit > 0:
        gen_state["total_target"] = min(gen_state["total_target"], limit)

    # Pre-load CAEN descriptions
    caen_map = {}
    caen_docs = await db.caen_codes.find({}, {"_id": 0, "cod": 1, "denumire": 1}).to_list(1000)
    for c in caen_docs:
        caen_map[c.get("cod", "")] = c.get("denumire", "")

    sem = asyncio.Semaphore(concurrency)
    batch_start = datetime.now(timezone.utc)

    # Cursor: active firms without seo_description, sorted by revenue (biggest first)
    cursor = db.firme.find(query, {"_id": 0, "cui": 1, "denumire": 1, "forma_juridica": 1,
                                    "judet": 1, "localitate": 1, "anaf_cod_caen": 1,
                                    "anaf_stare": 1, "mf_cifra_afaceri": 1, "mf_profit_net": 1,
                                    "mf_numar_angajati": 1, "mf_an_bilant": 1}).sort(
        "mf_cifra_afaceri", -1
    )

    if limit > 0:
        cursor = cursor.limit(limit)

    processed_total = 0

    async def process_one(company):
        nonlocal processed_total
        async with sem:
            if gen_state["should_stop"]:
                return

            cui = company.get("cui")
            caen = company.get("anaf_cod_caen", "")
            caen_desc = caen_map.get(str(caen)[:4], "")

            try:
                text = await _generate_one(api_key, company, caen_desc)
                if text and len(text) > 30:
                    await db.firme.update_one(
                        {"$or": [{"cui": str(cui)}, {"cui": cui}]},
                        {"$set": {
                            "seo_description": text,
                            "seo_generated_at": datetime.now(timezone.utc),
                        }},
                    )
                    gen_state["processed"] += 1
                else:
                    gen_state["skipped"] += 1
            except Exception as e:
                gen_state["errors"] += 1
                gen_state["last_error"] = f"CUI {cui}: {str(e)[:200]}"
                logger.warning(f"SEO gen error CUI={cui}: {e}")

            processed_total += 1
            gen_state["last_cui"] = cui

            # Update speed every 20 items
            if processed_total % 20 == 0:
                elapsed = (datetime.now(timezone.utc) - batch_start).total_seconds()
                if elapsed > 0:
                    gen_state["speed_per_min"] = round(processed_total / elapsed * 60, 1)

    # Process in batches of 50 to avoid loading everything in memory
    batch = []
    async for company in cursor:
        if gen_state["should_stop"]:
            break
        batch.append(company)
        if len(batch) >= 50:
            tasks = [process_one(c) for c in batch]
            await asyncio.gather(*tasks)
            batch = []

    # Process remaining
    if batch and not gen_state["should_stop"]:
        tasks = [process_one(c) for c in batch]
        await asyncio.gather(*tasks)

    gen_state["running"] = False
    logger.info(f"SEO generation finished: {gen_state['processed']} ok, {gen_state['errors']} errors")


class StartRequest(BaseModel):
    concurrency: int = 5
    limit: int = 0  # 0 = no limit


@router.post("/start")
async def start_generation(body: StartRequest = None, current_user=Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    if gen_state["running"]:
        raise HTTPException(status_code=409, detail="Generare deja în curs")

    body = body or StartRequest()
    conc = max(1, min(body.concurrency, 10))
    lim = max(0, body.limit)

    asyncio.create_task(_run_batch_generation(conc, lim))
    return {"status": "started", "concurrency": conc, "limit": lim}


@router.post("/stop")
async def stop_generation(current_user=Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    gen_state["should_stop"] = True
    return {"status": "stopping"}


@router.get("/status")
async def get_status(current_user=Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    db = get_local_db()
    # Fast count for seo_description (indexed field check only on small subset)
    total_with_seo = await db.firme.count_documents({"seo_description": {"$exists": True}})
    # Use cached/estimated count for total active (avoids full scan)
    try:
        total_est = await db.firme.estimated_document_count()
        # Rough estimate: ~97% are active
        total_active = int(total_est * 0.97)
    except Exception:
        total_active = 0

    return {
        **gen_state,
        "total_with_seo": total_with_seo,
        "total_active": total_active,
        "remaining": max(0, total_active - total_with_seo),
    }


@router.get("/preview/{cui}")
async def preview_seo(cui: str, current_user=Depends(get_current_user)):
    """Generate SEO text for a single company (preview, does NOT save)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY not set")

    db = get_local_db()
    company = await db.firme.find_one(
        {"$or": [{"cui": cui}, {"cui": int(cui) if cui.isdigit() else cui}]},
        {"_id": 0},
    )
    if not company:
        raise HTTPException(status_code=404, detail="Firma nu a fost găsită")

    caen = str(company.get("anaf_cod_caen", ""))[:4]
    caen_doc = await db.caen_codes.find_one({"cod": caen}, {"_id": 0, "denumire": 1})
    caen_desc = caen_doc.get("denumire", "") if caen_doc else ""

    text = await _generate_one(api_key, company, caen_desc)
    return {
        "cui": company.get("cui"),
        "denumire": company.get("denumire"),
        "seo_description": text,
    }
