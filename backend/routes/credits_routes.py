"""
Credits System Routes
Handles user credits, daily free views, and credit consumption
"""

from fastapi import APIRouter, HTTPException, Depends
from database import get_app_db
from auth import get_current_user, get_current_user_optional
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/credits", tags=["credits"])

# Configuration
DEFAULT_BONUS_CREDITS = 10
DEFAULT_DAILY_FREE_VIEWS = 5

# Credit packages
CREDIT_PACKAGES = [
    {"id": "pack_50", "credits": 50, "price": 9.99, "currency": "RON", "label": "50 Credite"},
    {"id": "pack_200", "credits": 200, "price": 29.99, "currency": "RON", "label": "200 Credite", "popular": True},
    {"id": "pack_500", "credits": 500, "price": 59.99, "currency": "RON", "label": "500 Credite", "best_value": True},
]


class ConsumeRequest(BaseModel):
    company_cui: str


async def get_or_create_user_credits(db, user_id: str):
    """Get user credits or create default record"""
    credits = await db.user_credits.find_one({"user_id": ObjectId(user_id)})
    
    if not credits:
        # Create new credits record with bonus
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        credits = {
            "user_id": ObjectId(user_id),
            "credits_balance": DEFAULT_BONUS_CREDITS,
            "free_views_today": DEFAULT_DAILY_FREE_VIEWS,
            "free_views_reset_date": today,
            "viewed_companies": [],
            "total_views": 0,
            "created_at": datetime.now(timezone.utc)
        }
        await db.user_credits.insert_one(credits)
    
    return credits


async def reset_daily_views_if_needed(db, credits: dict):
    """Reset daily free views if it's a new day"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if credits.get("free_views_reset_date") != today:
        await db.user_credits.update_one(
            {"_id": credits["_id"]},
            {
                "$set": {
                    "free_views_today": DEFAULT_DAILY_FREE_VIEWS,
                    "free_views_reset_date": today
                }
            }
        )
        credits["free_views_today"] = DEFAULT_DAILY_FREE_VIEWS
        credits["free_views_reset_date"] = today
    
    return credits


async def is_credits_system_enabled(db) -> bool:
    """Check if credits system is enabled in admin settings"""
    settings = await db.app_settings.find_one({"key": "credits_system_enabled"})
    if settings is None:
        # Default: enabled
        return True
    return settings.get("value", True)


@router.get("/status")
async def get_credits_status(current_user = Depends(get_current_user)):
    """Get user's credits status"""
    db = get_app_db()
    
    # Check if system is enabled
    system_enabled = await is_credits_system_enabled(db)
    
    # Get or create credits
    credits = await get_or_create_user_credits(db, current_user["user_id"])
    credits = await reset_daily_views_if_needed(db, credits)
    
    return {
        "system_enabled": system_enabled,
        "credits_balance": credits.get("credits_balance", 0),
        "free_views_today": credits.get("free_views_today", 0),
        "free_views_max": DEFAULT_DAILY_FREE_VIEWS,
        "total_views": credits.get("total_views", 0),
        "viewed_companies_count": len(credits.get("viewed_companies", []))
    }


@router.get("/packages")
async def get_credit_packages():
    """Get available credit packages"""
    db = get_app_db()
    system_enabled = await is_credits_system_enabled(db)
    
    return {
        "system_enabled": system_enabled,
        "packages": CREDIT_PACKAGES
    }


@router.post("/check-access")
async def check_company_access(
    request: ConsumeRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Check if user can access a company profile.
    Does NOT consume credits - just checks availability.
    """
    db = get_app_db()
    
    # Check if system is enabled
    system_enabled = await is_credits_system_enabled(db)
    
    if not system_enabled:
        return {
            "access_granted": True,
            "reason": "credits_system_disabled",
            "credits_balance": None,
            "free_views_today": None
        }
    
    # Not authenticated - limited preview (could show masked data)
    if not current_user:
        return {
            "access_granted": False,
            "reason": "not_authenticated",
            "message": "Autentifică-te pentru a vedea detaliile complete"
        }
    
    # Get user credits
    credits = await get_or_create_user_credits(db, current_user["user_id"])
    credits = await reset_daily_views_if_needed(db, credits)
    
    company_cui = request.company_cui
    viewed_companies = credits.get("viewed_companies", [])
    
    # Already viewed - always free
    if company_cui in viewed_companies:
        return {
            "access_granted": True,
            "reason": "already_viewed",
            "credits_balance": credits.get("credits_balance", 0),
            "free_views_today": credits.get("free_views_today", 0)
        }
    
    # Has free views today
    if credits.get("free_views_today", 0) > 0:
        return {
            "access_granted": True,
            "reason": "free_view_available",
            "will_consume": "free_view",
            "credits_balance": credits.get("credits_balance", 0),
            "free_views_today": credits.get("free_views_today", 0)
        }
    
    # Has credits
    if credits.get("credits_balance", 0) > 0:
        return {
            "access_granted": True,
            "reason": "credit_available",
            "will_consume": "credit",
            "credits_balance": credits.get("credits_balance", 0),
            "free_views_today": 0
        }
    
    # No credits, no free views
    return {
        "access_granted": False,
        "reason": "no_credits",
        "message": "Nu mai ai credite. Cumpără un pachet pentru a continua.",
        "credits_balance": 0,
        "free_views_today": 0
    }


@router.post("/consume")
async def consume_credit(
    request: ConsumeRequest,
    current_user = Depends(get_current_user)
):
    """
    Consume a credit or free view for accessing a company.
    Call this AFTER displaying the company data.
    """
    db = get_app_db()
    
    # Check if system is enabled
    system_enabled = await is_credits_system_enabled(db)
    
    if not system_enabled:
        return {
            "consumed": False,
            "reason": "credits_system_disabled"
        }
    
    # Get user credits
    credits = await get_or_create_user_credits(db, current_user["user_id"])
    credits = await reset_daily_views_if_needed(db, credits)
    
    company_cui = request.company_cui
    viewed_companies = credits.get("viewed_companies", [])
    
    # Already viewed - don't consume
    if company_cui in viewed_companies:
        return {
            "consumed": False,
            "reason": "already_viewed",
            "credits_balance": credits.get("credits_balance", 0),
            "free_views_today": credits.get("free_views_today", 0)
        }
    
    # Try free view first
    if credits.get("free_views_today", 0) > 0:
        await db.user_credits.update_one(
            {"_id": credits["_id"]},
            {
                "$inc": {"free_views_today": -1, "total_views": 1},
                "$push": {"viewed_companies": company_cui}
            }
        )
        return {
            "consumed": True,
            "type": "free_view",
            "credits_balance": credits.get("credits_balance", 0),
            "free_views_today": credits.get("free_views_today", 0) - 1
        }
    
    # Try credit
    if credits.get("credits_balance", 0) > 0:
        await db.user_credits.update_one(
            {"_id": credits["_id"]},
            {
                "$inc": {"credits_balance": -1, "total_views": 1},
                "$push": {"viewed_companies": company_cui}
            }
        )
        return {
            "consumed": True,
            "type": "credit",
            "credits_balance": credits.get("credits_balance", 0) - 1,
            "free_views_today": 0
        }
    
    # No credits available
    raise HTTPException(
        status_code=402,
        detail={
            "error": "no_credits",
            "message": "Nu mai ai credite disponibile"
        }
    )


@router.post("/add")
async def add_credits(
    credits_to_add: int,
    current_user = Depends(get_current_user)
):
    """
    Add credits to user account (called after successful payment).
    In production, this should be called from Stripe webhook.
    """
    db = get_app_db()
    
    if credits_to_add <= 0:
        raise HTTPException(status_code=400, detail="Invalid credits amount")
    
    # Get or create credits
    credits = await get_or_create_user_credits(db, current_user["user_id"])
    
    # Add credits
    await db.user_credits.update_one(
        {"_id": credits["_id"]},
        {"$inc": {"credits_balance": credits_to_add}}
    )
    
    # Log transaction
    await db.credit_transactions.insert_one({
        "user_id": ObjectId(current_user["user_id"]),
        "type": "purchase",
        "amount": credits_to_add,
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "credits_added": credits_to_add,
        "new_balance": credits.get("credits_balance", 0) + credits_to_add
    }


@router.get("/history")
async def get_credit_history(current_user = Depends(get_current_user)):
    """Get user's credit transaction history"""
    db = get_app_db()
    
    transactions = await db.credit_transactions.find(
        {"user_id": ObjectId(current_user["user_id"])}
    ).sort("created_at", -1).limit(50).to_list(length=50)
    
    return {
        "transactions": [
            {
                "type": t.get("type"),
                "amount": t.get("amount"),
                "created_at": t.get("created_at").isoformat() if t.get("created_at") else None
            }
            for t in transactions
        ]
    }
