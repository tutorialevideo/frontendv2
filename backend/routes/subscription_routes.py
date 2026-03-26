from fastapi import APIRouter, HTTPException, Depends, Request
from database import get_app_db
from auth import get_current_user
from models import (
    SubscriptionPlan, CheckoutRequest, CheckoutResponse,
    SubscriptionStatus
)
import stripe
import os
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

# Define subscription plans
PLANS = {
    "free": SubscriptionPlan(
        id="free",
        name="Free",
        price=0.0,
        currency="RON",
        interval="month",
        features=[
            "Căutare firme",
            "Date de bază",
            "Telefon mascat (074***)",
            "Căutări limitate"
        ]
    ),
    "plus": SubscriptionPlan(
        id="plus",
        name="Plus",
        price=49.0,
        currency="RON",
        interval="month",
        features=[
            "Toate din Free",
            "Mai multe căutări",
            "Favorite",
            "Istoric căutări",
            "Unele date premium"
        ],
        stripe_price_id="price_plus_monthly"
    ),
    "premium": SubscriptionPlan(
        id="premium",
        name="Premium",
        price=99.0,
        currency="RON",
        interval="month",
        features=[
            "Toate din Plus",
            "Telefon complet",
            "Administrator complet",
            "Export date",
            "Acces API",
            "Căutări nelimitate"
        ],
        stripe_price_id="price_premium_monthly"
    )
}

@router.get("/plans")
async def get_plans():
    """Get all subscription plans"""
    return {"plans": list(PLANS.values())}

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    checkout_req: CheckoutRequest,
    current_user = Depends(get_current_user),
    request: Request = None
):
    """Create Stripe checkout session"""
    
    # Validate plan
    if checkout_req.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan = PLANS[checkout_req.plan_id]
    
    if plan.price == 0:
        raise HTTPException(status_code=400, detail="Cannot checkout for free plan")
    
    # Initialize Stripe
    stripe_api_key = os.getenv("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe.api_key = stripe_api_key
    
    # Create success and cancel URLs
    success_url = f"{checkout_req.origin_url}/account/subscription?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_req.origin_url}/account/subscription"
    
    try:
        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'ron',
                    'product_data': {
                        'name': f'mFirme {plan.name}',
                        'description': f'Abonament {plan.name} lunar'
                    },
                    'unit_amount': int(plan.price * 100),  # Stripe uses cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': current_user["user_id"],
                'user_email': current_user["email"],
                'plan_id': plan.id,
                'plan_name': plan.name
            }
        )
        
        # Store payment transaction
        db = get_app_db()
        transaction = {
            "user_id": ObjectId(current_user["user_id"]),
            "session_id": session.id,
            "amount": plan.price,
            "currency": "ron",
            "plan_id": plan.id,
            "status": "pending",
            "payment_status": "pending",
            "metadata": {
                'user_id': current_user["user_id"],
                'user_email': current_user["email"],
                'plan_id': plan.id
            },
            "created_at": datetime.utcnow()
        }
        
        await db.payment_transactions.insert_one(transaction)
        
        return CheckoutResponse(url=session.url, session_id=session.id)
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get checkout session status and update subscription if paid"""
    
    stripe_api_key = os.getenv("STRIPE_API_KEY")
    stripe.api_key = stripe_api_key
    
    try:
        # Get session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        db = get_app_db()
        
        # Update transaction
        transaction = await db.payment_transactions.find_one({"session_id": session_id})
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        payment_status = "paid" if session.payment_status == "paid" else session.payment_status
        
        # Update transaction status
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": session.status,
                    "payment_status": payment_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # If payment successful and not already processed, upgrade user
        if payment_status == "paid" and transaction.get("payment_status") != "paid":
            plan_id = transaction["metadata"]["plan_id"]
            
            # Update user tier
            await db.users.update_one(
                {"_id": transaction["user_id"]},
                {
                    "$set": {
                        "tier": plan_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Create/update subscription record
            await db.subscriptions.update_one(
                {"user_id": transaction["user_id"]},
                {
                    "$set": {
                        "plan_id": plan_id,
                        "status": "active",
                        "stripe_session_id": session_id,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
        
        return {
            "status": session.status,
            "payment_status": payment_status,
            "amount": session.amount_total / 100 if session.amount_total else 0,
            "currency": session.currency
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/my-subscription", response_model=SubscriptionStatus)
async def get_my_subscription(current_user = Depends(get_current_user)):
    """Get current user's subscription status"""
    db = get_app_db()
    
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription = await db.subscriptions.find_one({"user_id": user["_id"]})
    
    return SubscriptionStatus(
        plan=user.get("tier", "free"),
        status=subscription.get("status", "inactive") if subscription else "inactive",
        current_period_end=subscription.get("current_period_end").isoformat() if subscription and subscription.get("current_period_end") else None
    )

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    
    stripe_api_key = os.getenv("STRIPE_API_KEY")
    stripe.api_key = stripe_api_key
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        else:
            event = stripe.Event.construct_from(
                stripe.util.convert_to_stripe_object(body.decode('utf-8')),
                stripe.api_key
            )
        
        # Handle webhook events
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            # Payment already handled in get_checkout_status
            pass
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
