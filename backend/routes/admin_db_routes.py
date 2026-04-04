"""
Admin DB Optimization Routes
Endpoints for database stats, index management, and optimization
"""

from fastapi import APIRouter, Depends
from auth import get_current_user
from database import get_local_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/db", tags=["admin-db"])

RECOMMENDED_INDEXES = [
    {
        "collection": "firme",
        "name": "judet_1",
        "keys": [("judet", 1)],
        "reason": "Cautare firme pe pagina de judet (Top Firme, filtrare)"
    },
    {
        "collection": "firme",
        "name": "localitate_1",
        "keys": [("localitate", 1)],
        "reason": "Cautare firme pe pagina de localitate"
    },
    {
        "collection": "firme",
        "name": "anaf_cod_caen_1",
        "keys": [("anaf_cod_caen", 1)],
        "reason": "Cautare firme pe pagina CAEN"
    },
    {
        "collection": "firme",
        "name": "mf_cifra_afaceri_-1",
        "keys": [("mf_cifra_afaceri", -1)],
        "reason": "Sortare Top Firme dupa cifra de afaceri (descrescator)"
    },
    {
        "collection": "firme",
        "name": "mf_profit_net_-1",
        "keys": [("mf_profit_net", -1)],
        "reason": "Sortare Top Firme dupa profit net"
    },
    {
        "collection": "firme",
        "name": "mf_numar_angajati_-1",
        "keys": [("mf_numar_angajati", -1)],
        "reason": "Sortare Top Firme dupa numar angajati"
    },
    {
        "collection": "firme",
        "name": "denumire_1",
        "keys": [("denumire", 1)],
        "reason": "Sortare alfabetica si cautare dupa denumire"
    },
    {
        "collection": "firme",
        "name": "judet_1_mf_cifra_afaceri_-1",
        "keys": [("judet", 1), ("mf_cifra_afaceri", -1)],
        "reason": "Index compus: Top Firme pe judet sortat dupa cifra afaceri (cel mai important)"
    },
    {
        "collection": "firme",
        "name": "anaf_cod_caen_1_mf_cifra_afaceri_-1",
        "keys": [("anaf_cod_caen", 1), ("mf_cifra_afaceri", -1)],
        "reason": "Index compus: Top Firme pe CAEN sortat dupa cifra afaceri"
    },
    {
        "collection": "dosare",
        "name": "cui_1",
        "keys": [("cui", 1)],
        "reason": "Cautare dosare per firma (pagina detalii firma)"
    },
    {
        "collection": "bpi_records",
        "name": "cui_1",
        "keys": [("cui", 1)],
        "reason": "Cautare BPI per firma (pagina detalii firma)"
    },
    {
        "collection": "users",
        "name": "email_1",
        "keys": [("email", 1)],
        "reason": "Cautare utilizator la autentificare"
    },
]


def _format_keys(keys):
    """Convert pymongo key list to readable string"""
    parts = []
    for k, d in keys:
        parts.append(f"{k} ({'ASC' if d == 1 else 'DESC'})")
    return ", ".join(parts)


@router.get("/stats")
async def get_db_stats(current_user=Depends(get_current_user)):
    """Get database statistics and index information"""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    db = get_local_db()
    collections_data = []
    total_data_size = 0
    total_index_size = 0

    target_collections = ["firme", "bilanturi", "dosare", "bpi_records", "users",
                          "caen_codes", "postal_codes", "api_keys", "audit_log"]

    for col_name in target_collections:
        try:
            stats = await db.command("collStats", col_name)
            indexes = await db[col_name].index_information()

            data_size = stats.get("size", 0)
            index_size = stats.get("totalIndexSize", 0)
            count = stats.get("count", 0)
            total_data_size += data_size
            total_index_size += index_size

            index_list = []
            for idx_name, idx_info in indexes.items():
                if idx_name == "_id_":
                    continue
                index_list.append({
                    "name": idx_name,
                    "keys": _format_keys(idx_info.get("key", [])),
                    "unique": idx_info.get("unique", False),
                })

            collections_data.append({
                "name": col_name,
                "count": count,
                "data_size_mb": round(data_size / 1024 / 1024, 1),
                "index_size_mb": round(index_size / 1024 / 1024, 1),
                "indexes": index_list,
                "index_count": len(index_list),
            })
        except Exception:
            collections_data.append({
                "name": col_name,
                "count": 0,
                "data_size_mb": 0,
                "index_size_mb": 0,
                "indexes": [],
                "index_count": 0,
            })

    # Check which recommended indexes are missing
    existing_index_names = {}
    for col in collections_data:
        existing_index_names[col["name"]] = {idx["name"] for idx in col["indexes"]}

    recommendations = []
    for rec in RECOMMENDED_INDEXES:
        col = rec["collection"]
        exists = rec["name"] in existing_index_names.get(col, set())
        recommendations.append({
            "collection": rec["collection"],
            "name": rec["name"],
            "keys": _format_keys(rec["keys"]),
            "reason": rec["reason"],
            "exists": exists,
            "priority": "critical" if "compus" in rec["reason"].lower() or "cifra" in rec["reason"].lower() else "recommended"
        })

    missing_count = sum(1 for r in recommendations if not r["exists"])

    return {
        "collections": collections_data,
        "total_data_size_mb": round(total_data_size / 1024 / 1024, 1),
        "total_index_size_mb": round(total_index_size / 1024 / 1024, 1),
        "recommendations": recommendations,
        "missing_indexes": missing_count,
        "total_recommended": len(recommendations),
        "health_score": round((1 - missing_count / max(len(recommendations), 1)) * 100),
    }


@router.post("/create-index")
async def create_single_index(body: dict, current_user=Depends(get_current_user)):
    """Create a single recommended index"""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    index_name = body.get("index_name")
    if not index_name:
        return {"error": "index_name required"}

    rec = next((r for r in RECOMMENDED_INDEXES if r["name"] == index_name), None)
    if not rec:
        return {"error": f"Unknown index: {index_name}"}

    db = get_local_db()
    try:
        result = await db[rec["collection"]].create_index(rec["keys"], name=rec["name"], background=True)
        logger.info(f"Created index {rec['name']} on {rec['collection']}: {result}")
        return {"status": "created", "index": rec["name"], "collection": rec["collection"], "result": str(result)}
    except Exception as e:
        logger.error(f"Failed to create index {rec['name']}: {e}")
        return {"error": str(e)}


@router.post("/create-all-indexes")
async def create_all_missing_indexes(current_user=Depends(get_current_user)):
    """Create all missing recommended indexes"""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    db = get_local_db()
    results = []

    for rec in RECOMMENDED_INDEXES:
        col_name = rec["collection"]
        try:
            existing = await db[col_name].index_information()
            if rec["name"] in existing:
                results.append({"index": rec["name"], "collection": col_name, "status": "exists"})
                continue

            await db[col_name].create_index(rec["keys"], name=rec["name"], background=True)
            results.append({"index": rec["name"], "collection": col_name, "status": "created"})
            logger.info(f"Created index {rec['name']} on {col_name}")
        except Exception as e:
            results.append({"index": rec["name"], "collection": col_name, "status": "error", "error": str(e)})
            logger.error(f"Failed to create index {rec['name']} on {col_name}: {e}")

    created = sum(1 for r in results if r["status"] == "created")
    existed = sum(1 for r in results if r["status"] == "exists")
    errors = sum(1 for r in results if r["status"] == "error")

    return {
        "total": len(results),
        "created": created,
        "already_existed": existed,
        "errors": errors,
        "details": results
    }


@router.post("/drop-index")
async def drop_index(body: dict, current_user=Depends(get_current_user)):
    """Drop a specific index"""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    collection = body.get("collection")
    index_name = body.get("index_name")
    if not collection or not index_name:
        return {"error": "collection and index_name required"}

    if index_name == "_id_":
        return {"error": "Cannot drop _id index"}

    db = get_local_db()
    try:
        await db[collection].drop_index(index_name)
        return {"status": "dropped", "collection": collection, "index": index_name}
    except Exception as e:
        return {"error": str(e)}
