"""
SEO Routes - Dynamic SEO Templates Management
Permite adminilor să configureze titluri și descrieri dinamice pentru pagini
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, timezone
from auth import get_current_user
from database import get_app_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/seo", tags=["seo"])


# === Models ===

class SeoTemplate(BaseModel):
    page_type: str  # company, search, caen_category, homepage
    title_template: str
    description_template: str
    index: bool = True  # index/noindex
    enabled: bool = True


class SeoTemplateUpdate(BaseModel):
    title_template: Optional[str] = None
    description_template: Optional[str] = None
    index: Optional[bool] = None
    enabled: Optional[bool] = None


# === Default Templates ===

DEFAULT_TEMPLATES = {
    "company": {
        "page_type": "company",
        "title_template": "{DENUMIRE} - CUI {CUI} | Date firmă, bilanțuri, contact",
        "description_template": "{DENUMIRE} (CUI: {CUI}) din {LOCALITATE}, {JUDET}. Activitate: {CAEN_DESCRIERE}. Vezi date complete, bilanțuri financiare și informații de contact.",
        "index": True,
        "enabled": True
    },
    "search": {
        "page_type": "search",
        "title_template": "Căutare firme: {QUERY} | RapoarteFirme.ro",
        "description_template": "Rezultate căutare pentru '{QUERY}'. Găsește firme românești, date financiare, bilanțuri și informații de contact.",
        "index": True,
        "enabled": True
    },
    "caen_category": {
        "page_type": "caen_category",
        "title_template": "Firme cu activitate {CAEN} - {CAEN_DESCRIERE} | RapoarteFirme.ro",
        "description_template": "Lista completă de firme cu cod CAEN {CAEN} ({CAEN_DESCRIERE}). Descoperă companii din acest domeniu de activitate.",
        "index": True,
        "enabled": True
    },
    "homepage": {
        "page_type": "homepage",
        "title_template": "RapoarteFirme.ro - Baza de date a firmelor din România",
        "description_template": "Caută printre 1.2 milioane de firme românești. Date financiare, bilanțuri, informații de contact și istoric complet.",
        "index": True,
        "enabled": True
    },
    "judet": {
        "page_type": "judet",
        "title_template": "Firme din județul {JUDET} | RapoarteFirme.ro",
        "description_template": "Vezi toate firmele înregistrate în județul {JUDET}. Date financiare, bilanțuri și informații complete.",
        "index": True,
        "enabled": True
    },
    "localitate": {
        "page_type": "localitate",
        "title_template": "Firme din {LOCALITATE}, {JUDET} | RapoarteFirme.ro",
        "description_template": "Descoperă firmele din {LOCALITATE}, județul {JUDET}. Informații complete, date financiare și contact.",
        "index": True,
        "enabled": True
    }
}


# === Available Variables ===

AVAILABLE_VARIABLES = [
    {"name": "DENUMIRE", "description": "Numele firmei", "applies_to": ["company"]},
    {"name": "CUI", "description": "Codul unic de identificare", "applies_to": ["company"]},
    {"name": "LOCALITATE", "description": "Localitatea/orașul firmei", "applies_to": ["company", "localitate"]},
    {"name": "JUDET", "description": "Județul", "applies_to": ["company", "judet", "localitate"]},
    {"name": "CAEN", "description": "Codul CAEN", "applies_to": ["company", "caen_category"]},
    {"name": "CAEN_DESCRIERE", "description": "Descrierea codului CAEN", "applies_to": ["company", "caen_category"]},
    {"name": "QUERY", "description": "Termenul de căutare", "applies_to": ["search"]},
    {"name": "AN", "description": "Anul (pentru bilanțuri)", "applies_to": ["company"]},
    {"name": "CIFRA_AFACERI", "description": "Cifra de afaceri formatată", "applies_to": ["company"]},
    {"name": "PROFIT", "description": "Profitul net formatat", "applies_to": ["company"]},
]


# === Helper Functions ===

async def verify_admin(current_user = Depends(get_current_user)):
    """Verify user is admin"""
    app_db = get_app_db()
    user = await app_db.users.find_one({"email": current_user["email"]})
    
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user


async def get_or_create_templates():
    """Get existing templates or create defaults"""
    app_db = get_app_db()
    
    templates = {}
    for page_type, default in DEFAULT_TEMPLATES.items():
        existing = await app_db.seo_settings.find_one({"page_type": page_type})
        if existing:
            existing.pop('_id', None)
            templates[page_type] = existing
        else:
            # Create default
            template_doc = {
                **default,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            await app_db.seo_settings.insert_one(template_doc)
            template_doc.pop('_id', None)
            templates[page_type] = template_doc
    
    return templates


# === Public Endpoints (for frontend to fetch SEO data) ===

@router.get("/templates/public")
async def get_public_templates():
    """Get all SEO templates (public - for frontend rendering)"""
    templates = await get_or_create_templates()
    return {
        "templates": templates,
        "variables": AVAILABLE_VARIABLES
    }


@router.get("/template/{page_type}")
async def get_template(page_type: str):
    """Get SEO template for a specific page type"""
    app_db = get_app_db()
    
    template = await app_db.seo_settings.find_one({"page_type": page_type})
    
    if not template:
        # Return default if exists
        if page_type in DEFAULT_TEMPLATES:
            return DEFAULT_TEMPLATES[page_type]
        raise HTTPException(status_code=404, detail=f"Template for '{page_type}' not found")
    
    template.pop('_id', None)
    return template


# === Admin Endpoints ===

@router.get("/admin/templates")
async def get_all_templates(admin_user = Depends(verify_admin)):
    """Get all SEO templates (admin)"""
    templates = await get_or_create_templates()
    return {
        "templates": templates,
        "variables": AVAILABLE_VARIABLES,
        "page_types": list(DEFAULT_TEMPLATES.keys())
    }


@router.put("/admin/template/{page_type}")
async def update_template(
    page_type: str,
    update: SeoTemplateUpdate,
    admin_user = Depends(verify_admin)
):
    """Update SEO template for a page type"""
    app_db = get_app_db()
    
    if page_type not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid page type: {page_type}")
    
    # Build update dict
    update_data = {"updated_at": datetime.now(timezone.utc)}
    
    if update.title_template is not None:
        update_data["title_template"] = update.title_template
    if update.description_template is not None:
        update_data["description_template"] = update.description_template
    if update.index is not None:
        update_data["index"] = update.index
    if update.enabled is not None:
        update_data["enabled"] = update.enabled
    
    result = await app_db.seo_settings.update_one(
        {"page_type": page_type},
        {"$set": update_data},
        upsert=True
    )
    
    # Log the change
    await app_db.audit_logs.insert_one({
        "action": "seo_template_update",
        "page_type": page_type,
        "changes": update.dict(exclude_none=True),
        "admin_email": admin_user.get("email"),
        "timestamp": datetime.now(timezone.utc)
    })
    
    logger.info(f"SEO template updated: {page_type} by {admin_user.get('email')}")
    
    # Return updated template
    updated = await app_db.seo_settings.find_one({"page_type": page_type})
    updated.pop('_id', None)
    
    return {
        "message": f"Template '{page_type}' updated successfully",
        "template": updated
    }


@router.post("/admin/reset/{page_type}")
async def reset_template(page_type: str, admin_user = Depends(verify_admin)):
    """Reset a template to default values"""
    app_db = get_app_db()
    
    if page_type not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid page type: {page_type}")
    
    default = DEFAULT_TEMPLATES[page_type]
    
    await app_db.seo_settings.update_one(
        {"page_type": page_type},
        {"$set": {
            **default,
            "updated_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )
    
    logger.info(f"SEO template reset to default: {page_type} by {admin_user.get('email')}")
    
    return {
        "message": f"Template '{page_type}' reset to default",
        "template": default
    }


@router.post("/admin/reset-all")
async def reset_all_templates(admin_user = Depends(verify_admin)):
    """Reset all templates to default values"""
    app_db = get_app_db()
    
    for page_type, default in DEFAULT_TEMPLATES.items():
        await app_db.seo_settings.update_one(
            {"page_type": page_type},
            {"$set": {
                **default,
                "updated_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )
    
    logger.info(f"All SEO templates reset by {admin_user.get('email')}")
    
    return {
        "message": "All templates reset to defaults",
        "templates": DEFAULT_TEMPLATES
    }


# === Preview Endpoint ===

@router.post("/preview")
async def preview_template(
    page_type: str,
    template: str,
    sample_data: Dict[str, str]
):
    """Preview a template with sample data"""
    result = template
    
    for key, value in sample_data.items():
        result = result.replace(f"{{{key}}}", value)
    
    return {
        "original": template,
        "rendered": result,
        "sample_data": sample_data
    }
