from fastapi import APIRouter, HTTPException, Depends
from database import get_app_db, get_companies_db
from auth import get_current_user
from bson import ObjectId
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/admin", tags=["admin"])

async def verify_admin(current_user = Depends(get_current_user)):
    """Verify user is admin"""
    db = get_app_db()
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user

@router.get("/stats")
async def get_admin_stats(admin_user = Depends(verify_admin)):
    """Get admin dashboard statistics"""
    app_db = get_app_db()
    companies_db = get_companies_db()
    
    # User stats
    total_users = await app_db.users.count_documents({})
    free_users = await app_db.users.count_documents({"tier": "free"})
    plus_users = await app_db.users.count_documents({"tier": "plus"})
    premium_users = await app_db.users.count_documents({"tier": "premium"})
    
    # Registration stats (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users = await app_db.users.count_documents({
        "created_at": {"$gte": thirty_days_ago}
    })
    
    # Favorites stats
    total_favorites = await app_db.favorites.count_documents({})
    
    # Payment stats
    total_transactions = await app_db.payment_transactions.count_documents({})
    paid_transactions = await app_db.payment_transactions.count_documents({
        "payment_status": "paid"
    })
    
    # Revenue calculation (from paid transactions)
    revenue_pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    revenue_result = await app_db.payment_transactions.aggregate(revenue_pipeline).to_list(length=1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Companies stats
    total_companies = await companies_db.firme.count_documents({})
    
    return {
        "users": {
            "total": total_users,
            "free": free_users,
            "plus": plus_users,
            "premium": premium_users,
            "new_last_30_days": new_users
        },
        "engagement": {
            "total_favorites": total_favorites,
            "avg_favorites_per_user": round(total_favorites / total_users, 2) if total_users > 0 else 0
        },
        "revenue": {
            "total_transactions": total_transactions,
            "paid_transactions": paid_transactions,
            "total_revenue_ron": round(total_revenue, 2)
        },
        "platform": {
            "total_companies": total_companies
        }
    }

@router.get("/users")
async def get_users(admin_user = Depends(verify_admin), skip: int = 0, limit: int = 50):
    """Get all users (paginated)"""
    app_db = get_app_db()
    
    users = await app_db.users.find().sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    total = await app_db.users.count_documents({})
    
    users_data = []
    for user in users:
        users_data.append({
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "tier": user.get("tier", "free"),
            "role": user.get("role", "user"),
            "created_at": user["created_at"].isoformat()
        })
    
    return {
        "users": users_data,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/transactions")
async def get_transactions(admin_user = Depends(verify_admin), skip: int = 0, limit: int = 50):
    """Get payment transactions"""
    app_db = get_app_db()
    
    transactions = await app_db.payment_transactions.find().sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    total = await app_db.payment_transactions.count_documents({})
    
    trans_data = []
    for trans in transactions:
        trans_data.append({
            "id": str(trans["_id"]),
            "session_id": trans.get("session_id"),
            "amount": trans.get("amount"),
            "currency": trans.get("currency"),
            "plan_id": trans.get("plan_id"),
            "status": trans.get("status"),
            "payment_status": trans.get("payment_status"),
            "user_email": trans.get("metadata", {}).get("user_email"),
            "created_at": trans["created_at"].isoformat()
        })
    
    return {
        "transactions": trans_data,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ============ SETTINGS ENDPOINTS ============

@router.get("/settings")
async def get_admin_settings(admin_user = Depends(verify_admin)):
    """Get all admin settings"""
    app_db = get_app_db()
    
    # Get credits system setting
    credits_setting = await app_db.app_settings.find_one({"key": "credits_system_enabled"})
    credits_enabled = credits_setting.get("value", True) if credits_setting else True
    
    # Get credit packages setting (could be customizable in future)
    
    return {
        "credits_system_enabled": credits_enabled,
        "default_bonus_credits": 10,
        "default_daily_free_views": 5,
        "credit_packages": [
            {"id": "pack_50", "credits": 50, "price": 9.99},
            {"id": "pack_200", "credits": 200, "price": 29.99},
            {"id": "pack_500", "credits": 500, "price": 59.99},
        ]
    }


@router.post("/settings/credits-system/toggle")
async def toggle_credits_system(admin_user = Depends(verify_admin)):
    """Toggle credits system on/off"""
    app_db = get_app_db()
    
    # Get current state
    setting = await app_db.app_settings.find_one({"key": "credits_system_enabled"})
    current_value = setting.get("value", True) if setting else True
    new_value = not current_value
    
    # Update or insert
    await app_db.app_settings.update_one(
        {"key": "credits_system_enabled"},
        {
            "$set": {
                "key": "credits_system_enabled",
                "value": new_value,
                "updated_at": datetime.utcnow(),
                "updated_by": str(admin_user["_id"])
            }
        },
        upsert=True
    )
    
    # Log the action
    await app_db.audit_logs.insert_one({
        "admin_id": admin_user["_id"],
        "admin_email": admin_user.get("email"),
        "action": "toggle_credits_system",
        "details": {"new_value": new_value},
        "created_at": datetime.utcnow()
    })
    
    return {
        "success": True,
        "credits_system_enabled": new_value,
        "message": f"Sistemul de credite a fost {'activat' if new_value else 'dezactivat'}"
    }


@router.get("/credits/stats")
async def get_credits_stats(admin_user = Depends(verify_admin)):
    """Get credits system statistics"""
    app_db = get_app_db()
    
    # Total users with credits
    total_credit_users = await app_db.user_credits.count_documents({})
    
    # Total credits in circulation
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$credits_balance"}}}
    ]
    credits_result = await app_db.user_credits.aggregate(pipeline).to_list(length=1)
    total_credits = credits_result[0]["total"] if credits_result else 0
    
    # Total views
    views_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$total_views"}}}
    ]
    views_result = await app_db.user_credits.aggregate(views_pipeline).to_list(length=1)
    total_views = views_result[0]["total"] if views_result else 0
    
    # Credit transactions
    total_purchases = await app_db.credit_transactions.count_documents({"type": "purchase"})
    
    return {
        "total_users_with_credits": total_credit_users,
        "total_credits_in_circulation": total_credits,
        "total_company_views": total_views,
        "total_credit_purchases": total_purchases
    }
