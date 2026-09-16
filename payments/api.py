"""Payment and subscription API endpoints."""

from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional
from pydantic import BaseModel, Field

from .plans import list_plans, get_plan_by_id, PlanTier
from .stripe_handler import stripe_handler
from .credits import credit_manager, CreditType
from .billing import billing_manager

router = APIRouter(prefix="/api/billing", tags=["billing"])


# --- Request Models ---

class SubscribeRequest(BaseModel):
    plan_id: str
    billing_cycle: str = "monthly"  # monthly or yearly


class BuyCreditsRequest(BaseModel):
    credits: int = Field(ge=100, le=100000)
    payment_method_id: Optional[str] = None


class UpgradeRequest(BaseModel):
    new_plan_id: str


# --- Plan Endpoints ---

@router.get("/plans")
async def get_plans():
    """List all available subscription plans."""
    return {"plans": list_plans()}


@router.get("/plans/{plan_id}")
async def get_plan_details(plan_id: str):
    """Get details of a specific plan."""
    plan = get_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {
        "id": plan.id,
        "name": plan.name,
        "tier": plan.tier.value,
        "price_monthly": plan.price_monthly,
        "price_yearly": plan.price_yearly,
        "credits_monthly": plan.credits_monthly,
        "features": plan.features,
        "services": [
            {
                "type": s.service_type,
                "monthly_limit": s.monthly_limit,
                "daily_limit": s.daily_limit,
            }
            for s in plan.services
        ],
    }


# --- Subscription Endpoints ---

@router.post("/subscribe")
async def subscribe(request: SubscribeRequest):
    """Subscribe to a plan."""
    plan = get_plan_by_id(request.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.tier == PlanTier.FREE:
        # Free plan - no payment needed
        return {
            "status": "active",
            "plan": plan.id,
            "message": "Free plan activated",
        }

    # Would create Stripe subscription here
    price = plan.price_monthly if request.billing_cycle == "monthly" else plan.price_yearly

    return {
        "status": "pending",
        "plan": plan.id,
        "price": price,
        "billing_cycle": request.billing_cycle,
        "checkout_url": "/api/billing/checkout",  # Would be Stripe checkout URL
        "message": "Complete payment to activate subscription",
    }


@router.post("/subscribe/cancel")
async def cancel_subscription():
    """Cancel current subscription."""
    return {
        "status": "cancelled",
        "message": "Subscription will be cancelled at end of billing period",
    }


@router.get("/subscription")
async def get_subscription():
    """Get current subscription details."""
    # Would get from database
    return {
        "plan": "pro",
        "status": "active",
        "current_period_end": "2026-10-16T00:00:00",
        "auto_renew": True,
    }


# --- Credit Endpoints ---

@router.get("/credits")
async def get_credits():
    """Get credit balance."""
    # Would get user_id from auth
    return credit_manager.get_balance("user_123")


@router.post("/credits/buy")
async def buy_credits(request: BuyCreditsRequest):
    """Purchase additional credits."""
    # Calculate price (e.g., $0.01 per credit)
    price = request.credits * 0.01

    # Would create Stripe payment intent here

    return {
        "credits": request.credits,
        "price": price,
        "currency": "usd",
        "payment_pending": True,
        "message": "Complete payment to add credits",
    }


@router.post("/credits/use")
async def use_credits(service: str, tokens: int = 0):
    """Use credits for a generation (internal endpoint)."""
    # Calculate credit cost
    estimate = credit_manager.estimate_cost(service, tokens=tokens)
    cost = estimate["estimated_credits"]

    result = credit_manager.use_credits("user_123", cost, service)
    return result


# --- Billing Endpoints ---

@router.get("/invoices")
async def get_invoices(limit: int = 20):
    """Get billing history."""
    return {
        "invoices": billing_manager.get_invoices("user_123", limit)
    }


@router.get("/invoices/summary")
async def get_billing_summary():
    """Get billing summary."""
    return billing_manager.get_billing_summary("user_123")


@router.get("/payment-methods")
async def get_payment_methods():
    """Get saved payment methods."""
    return {
        "methods": billing_manager.get_payment_methods("user_123")
    }


@router.post("/payment-methods")
async def add_payment_method(method_type: str, last_four: str):
    """Add a payment method."""
    method = billing_manager.add_payment_method("user_123", method_type, last_four)
    return {"method": method}


# --- Stripe Webhook ---

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    result = await stripe_handler.handle_webhook(payload, sig_header)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# --- Comparison Endpoint ---

@router.get("/compare")
async def compare_plans():
    """Compare all plans side by side."""
    plans = list_plans()
    return {
        "plans": plans,
        "recommendations": {
            "individual": "starter",
            "small_team": "pro",
            "business": "business",
            "enterprise": "enterprise",
        },
    }