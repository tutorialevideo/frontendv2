"""
Elasticsearch Routes for mFirme
Handles indexing, searching, and management of Elasticsearch
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from database import get_app_db, get_companies_db
from auth import get_current_user
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional, List
import os
import asyncio
import httpx
import json
import re

router = APIRouter(prefix="/api/elasticsearch", tags=["elasticsearch"])

# Elasticsearch Configuration
ES_HOST = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
ES_INDEX_COMPANIES = "mfirme_companies"

# Index mapping for companies
COMPANIES_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "romanian_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "romanian_stop", "romanian_stemmer", "asciifolding"]
                },
                "fuzzy_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding", "edge_ngram_filter"]
                }
            },
            "filter": {
                "romanian_stop": {
                    "type": "stop",
                    "stopwords": "_romanian_"
                },
                "romanian_stemmer": {
                    "type": "stemmer",
                    "language": "romanian"
                },
                "edge_ngram_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "cui": {"type": "keyword"},
            "denumire": {
                "type": "text",
                "analyzer": "romanian_analyzer",
                "fields": {
                    "fuzzy": {"type": "text", "analyzer": "fuzzy_analyzer"},
                    "keyword": {"type": "keyword"}
                }
            },
            "denumire_suggest": {
                "type": "completion",
                "analyzer": "simple"
            },
            "judet": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "localitate": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "adresa": {"type": "text", "analyzer": "romanian_analyzer"},
            "anaf_cod_caen": {"type": "keyword"},
            "caen_denumire": {"type": "text", "analyzer": "romanian_analyzer"},
            "forma_juridica": {"type": "keyword"},
            "anaf_stare": {"type": "keyword"},
            "administrator": {"type": "text", "analyzer": "romanian_analyzer"},
            "asociati": {"type": "text", "analyzer": "romanian_analyzer"},
            "telefon": {"type": "keyword"},
            "email": {"type": "keyword"},
            "website": {"type": "keyword"},
            "mf_cifra_afaceri": {"type": "long"},
            "mf_profit_net": {"type": "long"},
            "mf_numar_angajati": {"type": "integer"},
            "mf_an_bilant": {"type": "integer"},
            "data_inregistrare": {"type": "date", "format": "yyyy-MM-dd||yyyy-MM-dd'T'HH:mm:ss||epoch_millis"},
            "indexed_at": {"type": "date"}
        }
    }
}


class SearchRequest(BaseModel):
    query: str
    judet: Optional[str] = None
    localitate: Optional[str] = None
    caen: Optional[str] = None
    stare: Optional[str] = None
    page: int = 1
    limit: int = 20
    fuzzy: bool = True


class IndexingStatus(BaseModel):
    is_running: bool
    total_documents: int
    indexed_documents: int
    progress_percent: float
    started_at: Optional[str]
    estimated_remaining: Optional[str]


# Global indexing state
indexing_state = {
    "is_running": False,
    "total": 0,
    "indexed": 0,
    "started_at": None,
    "errors": []
}


async def es_request(method: str, path: str, body: dict = None, timeout: float = 30.0):
    """Make async request to Elasticsearch"""
    async with httpx.AsyncClient(timeout=timeout) as client:
        url = f"{ES_HOST}{path}"
        headers = {"Content-Type": "application/json"}
        
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=body)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=body)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        elif method == "HEAD":
            response = await client.head(url, headers=headers)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return response


async def check_es_connection():
    """Check if Elasticsearch is available"""
    try:
        response = await es_request("GET", "/")
        return response.status_code == 200
    except:
        return False


@router.get("/status")
async def get_elasticsearch_status(current_user = Depends(get_current_user)):
    """Get Elasticsearch cluster status and index info"""
    db = get_app_db()
    
    # Check admin role
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = {
        "connected": False,
        "cluster": None,
        "index": None,
        "indexing": {
            "is_running": indexing_state["is_running"],
            "total": indexing_state["total"],
            "indexed": indexing_state["indexed"],
            "progress_percent": round((indexing_state["indexed"] / indexing_state["total"] * 100) if indexing_state["total"] > 0 else 0, 2),
            "started_at": indexing_state["started_at"],
            "errors_count": len(indexing_state["errors"])
        }
    }
    
    try:
        # Check connection
        response = await es_request("GET", "/_cluster/health")
        if response.status_code == 200:
            result["connected"] = True
            result["cluster"] = response.json()
        
        # Check index
        index_response = await es_request("GET", f"/{ES_INDEX_COMPANIES}/_stats")
        if index_response.status_code == 200:
            stats = index_response.json()
            index_stats = stats.get("indices", {}).get(ES_INDEX_COMPANIES, {})
            primaries = index_stats.get("primaries", {})
            result["index"] = {
                "name": ES_INDEX_COMPANIES,
                "exists": True,
                "docs_count": primaries.get("docs", {}).get("count", 0),
                "size_bytes": primaries.get("store", {}).get("size_in_bytes", 0),
                "size_human": f"{primaries.get('store', {}).get('size_in_bytes', 0) / 1024 / 1024:.2f} MB"
            }
        else:
            result["index"] = {"name": ES_INDEX_COMPANIES, "exists": False}
            
    except Exception as e:
        result["error"] = str(e)
    
    return result


@router.post("/create-index")
async def create_index(current_user = Depends(get_current_user)):
    """Create the companies index with proper mapping"""
    db = get_app_db()
    
    # Check admin role
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not await check_es_connection():
        raise HTTPException(status_code=503, detail="Elasticsearch nu este disponibil")
    
    try:
        # Delete existing index if exists
        await es_request("DELETE", f"/{ES_INDEX_COMPANIES}")
        
        # Create new index
        response = await es_request("PUT", f"/{ES_INDEX_COMPANIES}", COMPANIES_INDEX_MAPPING)
        
        if response.status_code in [200, 201]:
            return {"success": True, "message": "Index creat cu succes!"}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-indexing")
async def start_indexing(background_tasks: BackgroundTasks, current_user = Depends(get_current_user)):
    """Start background indexing of all companies"""
    global indexing_state
    
    db = get_app_db()
    
    # Check admin role
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not await check_es_connection():
        raise HTTPException(status_code=503, detail="Elasticsearch nu este disponibil")
    
    if indexing_state["is_running"]:
        raise HTTPException(status_code=409, detail="Indexarea este deja în curs")
    
    # Start background indexing
    background_tasks.add_task(run_indexing)
    
    return {
        "success": True,
        "message": "Indexarea a început în background. Verifică progresul în pagina de status."
    }


async def run_indexing():
    """Background task to index all companies"""
    global indexing_state
    
    indexing_state["is_running"] = True
    indexing_state["started_at"] = datetime.now(timezone.utc).isoformat()
    indexing_state["errors"] = []
    indexing_state["indexed"] = 0
    
    try:
        companies_db = get_companies_db()
        
        # Get total count
        total = await companies_db.firme.count_documents({})
        indexing_state["total"] = total
        
        # Get CAEN codes for enrichment
        caen_codes = {}
        async for caen in companies_db.caen_codes.find({}):
            caen_codes[caen.get("cod")] = caen.get("denumire", "")
        
        # Process in batches
        batch_size = 500
        batch = []
        processed = 0
        
        async for company in companies_db.firme.find({}):
            # Prepare document for ES
            doc = prepare_company_document(company, caen_codes)
            
            # Add to batch (bulk format)
            batch.append({"index": {"_index": ES_INDEX_COMPANIES, "_id": doc["cui"]}})
            batch.append(doc)
            
            if len(batch) >= batch_size * 2:  # Each doc has 2 lines in bulk
                await bulk_index(batch)
                processed += batch_size
                indexing_state["indexed"] = processed
                batch = []
        
        # Index remaining
        if batch:
            await bulk_index(batch)
            indexing_state["indexed"] = total
        
        # Refresh index
        await es_request("POST", f"/{ES_INDEX_COMPANIES}/_refresh")
        
    except Exception as e:
        indexing_state["errors"].append(str(e))
    finally:
        indexing_state["is_running"] = False


def prepare_company_document(company: dict, caen_codes: dict) -> dict:
    """Prepare a company document for Elasticsearch indexing"""
    cui = company.get("cui", "")
    denumire = company.get("denumire", "")
    cod_caen = company.get("anaf_cod_caen", "")
    
    # Get CAEN description
    caen_denumire = ""
    if cod_caen and len(cod_caen) >= 4:
        caen_denumire = caen_codes.get(cod_caen[:4], "")
    
    # Parse date
    data_inreg = None
    if company.get("data_inregistrare"):
        try:
            if isinstance(company["data_inregistrare"], datetime):
                data_inreg = company["data_inregistrare"].strftime("%Y-%m-%d")
            elif isinstance(company["data_inregistrare"], str):
                data_inreg = company["data_inregistrare"][:10]
        except:
            pass
    
    return {
        "cui": cui,
        "denumire": denumire,
        "denumire_suggest": denumire,
        "judet": company.get("judet", ""),
        "localitate": company.get("localitate", ""),
        "adresa": company.get("anaf_adresa") or company.get("adresa", ""),
        "anaf_cod_caen": cod_caen,
        "caen_denumire": caen_denumire,
        "forma_juridica": company.get("forma_juridica", ""),
        "anaf_stare": company.get("anaf_stare", ""),
        "administrator": company.get("administrator", ""),
        "asociati": company.get("asociati", ""),
        "telefon": company.get("telefon", ""),
        "email": company.get("email", ""),
        "website": company.get("website", ""),
        "mf_cifra_afaceri": safe_int(company.get("mf_cifra_afaceri")),
        "mf_profit_net": safe_int(company.get("mf_profit_net")),
        "mf_numar_angajati": safe_int(company.get("mf_numar_angajati")),
        "mf_an_bilant": safe_int(company.get("mf_an_bilant")),
        "data_inregistrare": data_inreg,
        "indexed_at": datetime.now(timezone.utc).isoformat()
    }


def safe_int(value):
    """Safely convert to int"""
    if value is None:
        return None
    try:
        return int(value)
    except:
        return None


async def bulk_index(batch: list):
    """Bulk index documents to Elasticsearch"""
    # Convert to NDJSON format
    body = "\n".join(json.dumps(item) for item in batch) + "\n"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{ES_HOST}/_bulk",
            content=body,
            headers={"Content-Type": "application/x-ndjson"}
        )
        
        if response.status_code not in [200, 201]:
            indexing_state["errors"].append(f"Bulk error: {response.text[:200]}")


@router.post("/stop-indexing")
async def stop_indexing(current_user = Depends(get_current_user)):
    """Stop the indexing process"""
    global indexing_state
    
    db = get_app_db()
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    indexing_state["is_running"] = False
    return {"success": True, "message": "Indexarea a fost oprită"}


@router.post("/search")
async def search_companies(request: SearchRequest):
    """Search companies using Elasticsearch with fuzzy matching"""
    
    if not await check_es_connection():
        # Fallback to MongoDB if ES is not available
        raise HTTPException(status_code=503, detail="Elasticsearch nu este disponibil. Folosește căutarea standard.")
    
    # Build query
    must_clauses = []
    filter_clauses = []
    
    if request.query:
        query_clean = request.query.strip()
        
        # Check if it's a CUI search
        if query_clean.isdigit():
            must_clauses.append({
                "prefix": {"cui": query_clean}
            })
        else:
            # Fuzzy search on multiple fields
            if request.fuzzy:
                must_clauses.append({
                    "multi_match": {
                        "query": query_clean,
                        "fields": [
                            "denumire^3",
                            "denumire.fuzzy^2",
                            "adresa",
                            "administrator",
                            "asociati",
                            "localitate",
                            "caen_denumire"
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                        "prefix_length": 2,
                        "operator": "or"
                    }
                })
            else:
                must_clauses.append({
                    "multi_match": {
                        "query": query_clean,
                        "fields": ["denumire^3", "adresa", "administrator", "localitate"],
                        "type": "phrase_prefix"
                    }
                })
    
    # Filters
    if request.judet:
        filter_clauses.append({"term": {"judet.keyword": request.judet}})
    
    if request.localitate:
        filter_clauses.append({"match": {"localitate": request.localitate}})
    
    if request.caen:
        filter_clauses.append({"prefix": {"anaf_cod_caen": request.caen}})
    
    if request.stare:
        filter_clauses.append({"term": {"anaf_stare": request.stare}})
    
    # Build final query
    es_query = {
        "query": {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "filter": filter_clauses
            }
        },
        "from": (request.page - 1) * request.limit,
        "size": request.limit,
        "highlight": {
            "fields": {
                "denumire": {},
                "adresa": {},
                "administrator": {},
                "localitate": {}
            },
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"]
        },
        "sort": [
            {"_score": "desc"},
            {"mf_cifra_afaceri": {"order": "desc", "missing": "_last"}}
        ]
    }
    
    try:
        response = await es_request("POST", f"/{ES_INDEX_COMPANIES}/_search", es_query)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"ES Error: {response.text}")
        
        data = response.json()
        hits = data.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        
        results = []
        for hit in hits.get("hits", []):
            source = hit.get("_source", {})
            highlight = hit.get("highlight", {})
            
            results.append({
                "cui": source.get("cui"),
                "denumire": source.get("denumire"),
                "denumire_highlight": highlight.get("denumire", [source.get("denumire")])[0] if highlight.get("denumire") else None,
                "judet": source.get("judet"),
                "localitate": source.get("localitate"),
                "adresa": source.get("adresa"),
                "anaf_cod_caen": source.get("anaf_cod_caen"),
                "caen_denumire": source.get("caen_denumire"),
                "forma_juridica": source.get("forma_juridica"),
                "anaf_stare": source.get("anaf_stare"),
                "mf_cifra_afaceri": source.get("mf_cifra_afaceri"),
                "mf_numar_angajati": source.get("mf_numar_angajati"),
                "mf_an_bilant": source.get("mf_an_bilant"),
                "score": hit.get("_score")
            })
        
        return {
            "success": True,
            "data": {
                "results": results,
                "pagination": {
                    "total": total,
                    "page": request.page,
                    "pages": (total + request.limit - 1) // request.limit,
                    "limit": request.limit
                }
            },
            "search_engine": "elasticsearch"
        }
        
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Elasticsearch connection error: {str(e)}")


@router.get("/search/simple")
async def simple_search(
    q: str = Query(..., min_length=1),
    judet: Optional[str] = None,
    localitate: Optional[str] = None,
    caen: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Simple GET endpoint for search (for frontend integration)"""
    request = SearchRequest(
        query=q,
        judet=judet,
        localitate=localitate,
        caen=caen,
        page=page,
        limit=limit,
        fuzzy=True
    )
    return await search_companies(request)


@router.delete("/delete-index")
async def delete_index(current_user = Depends(get_current_user)):
    """Delete the companies index"""
    db = get_app_db()
    
    # Check admin role
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not await check_es_connection():
        raise HTTPException(status_code=503, detail="Elasticsearch nu este disponibil")
    
    try:
        response = await es_request("DELETE", f"/{ES_INDEX_COMPANIES}")
        return {"success": True, "message": "Index șters cu succes!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_elasticsearch_config(current_user = Depends(get_current_user)):
    """Get Elasticsearch configuration info"""
    db = get_app_db()
    
    # Check admin role  
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "es_host": ES_HOST,
        "index_name": ES_INDEX_COMPANIES,
        "docker_compose_path": "/app/docker/docker-compose.elasticsearch.yml",
        "setup_script": "/app/docker/setup-elasticsearch.sh",
        "setup_commands": [
            "cd /app/docker",
            "chmod +x setup-elasticsearch.sh",
            "./setup-elasticsearch.sh"
        ]
    }
