"""Subscription plans and pricing tiers."""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional


class PlanTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


@dataclass
class ServiceAllocation:
    """Allocation for a specific service in a plan."""
    service_type: str  # text, image, video, 3d
    monthly_limit: int  # Number of generations
    daily_limit: int
    max_tokens_per_request: int = 0  # 0 = unlimited within allocation
    priority: int = 0  # Higher = better quality models
    rate_limit_per_minute: int = 10


@dataclass
class SubscriptionPlan:
    """Define a subscription plan."""
    id: str
    name: str
    tier: PlanTier
    price_monthly: float  # USD
    price_yearly: float  # USD (discounted)
    credits_monthly: int  # Base credits included
    credits_per_dollar: float  # Extra credits per $1 spent
    services: List[ServiceAllocation] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    max_concurrent: int = 1  # Max concurrent requests
    support_level: str = "email"  # email, chat, priority, dedicated
    api_access: bool = True
    webhook_access: bool = False
    custom_models: bool = False
    sla_uptime: float = 99.0  # Guaranteed uptime %

    @property
    def price_per_credit(self) -> float:
        """Cost per credit."""
        if self.credits_monthly == 0:
            return 0
        return self.price_monthly / self.credits_monthly

    def get_service_allocation(self, service_type: str) -> Optional[ServiceAllocation]:
        """Get allocation for a specific service."""
        for alloc in self.services:
            if alloc.service_type == service_type:
                return alloc
        return None


# Define all plans
plans = {
    PlanTier.FREE: SubscriptionPlan(
        id="free",
        name="Free",
        tier=PlanTier.FREE,
        price_monthly=0,
        price_yearly=0,
        credits_monthly=100,
        credits_per_dollar=0,
        services=[
            ServiceAllocation("text", monthly_limit=50, daily_limit=10, max_tokens_per_request=512, rate_limit_per_minute=5),
            ServiceAllocation("image", monthly_limit=10, daily_limit=3, rate_limit_per_minute=1),
            ServiceAllocation("video", monthly_limit=0, daily_limit=0),
            ServiceAllocation("3d", monthly_limit=0, daily_limit=0),
        ],
        features=[
            "Basic text generation",
            "5 image generations/month",
            "Community support",
            "Web interface only",
        ],
        max_concurrent=1,
        support_level="community",
        api_access=False,
        sla_uptime=95.0,
    ),

    PlanTier.STARTER: SubscriptionPlan(
        id="starter",
        name="Starter",
        tier=PlanTier.STARTER,
        price_monthly=9.99,
        price_yearly=99.99,  # 2 months free
        credits_monthly=1000,
        credits_per_dollar=100,
        services=[
            ServiceAllocation("text", monthly_limit=500, daily_limit=50, max_tokens_per_request=2048, rate_limit_per_minute=20),
            ServiceAllocation("image", monthly_limit=100, daily_limit=10, rate_limit_per_minute=5),
            ServiceAllocation("video", monthly_limit=5, daily_limit=2),
            ServiceAllocation("3d", monthly_limit=2, daily_limit=1),
        ],
        features=[
            "All text models",
            "100 images/month",
            "5 videos/month",
            "API access",
            "Email support",
            "Generation history",
        ],
        max_concurrent=2,
        support_level="email",
        api_access=True,
        sla_uptime=99.0,
    ),

    PlanTier.PRO: SubscriptionPlan(
        id="pro",
        name="Pro",
        tier=PlanTier.PRO,
        price_monthly=29.99,
        price_yearly=299.99,
        credits_monthly=5000,
        credits_per_dollar=200,
        services=[
            ServiceAllocation("text", monthly_limit=2000, daily_limit=200, max_tokens_per_request=4096, rate_limit_per_minute=60, priority=1),
            ServiceAllocation("image", monthly_limit=500, daily_limit=50, rate_limit_per_minute=15),
            ServiceAllocation("video", monthly_limit=25, daily_limit=5, priority=1),
            ServiceAllocation("3d", monthly_limit=10, daily_limit=3),
        ],
        features=[
            "All models including GPT-4",
            "500 images/month",
            "25 videos/month",
            "Priority processing",
            "Chat support",
            "Webhooks",
            "Custom styles",
            "Batch processing",
        ],
        max_concurrent=5,
        support_level="chat",
        api_access=True,
        webhook_access=True,
        sla_uptime=99.5,
    ),

    PlanTier.BUSINESS: SubscriptionPlan(
        id="business",
        name="Business",
        tier=PlanTier.BUSINESS,
        price_monthly=99.99,
        price_yearly=999.99,
        credits_monthly=20000,
        credits_per_dollar=300,
        services=[
            ServiceAllocation("text", monthly_limit=10000, daily_limit=1000, max_tokens_per_request=8192, rate_limit_per_minute=200, priority=2),
            ServiceAllocation("image", monthly_limit=2000, daily_limit=200, rate_limit_per_minute=50, priority=1),
            ServiceAllocation("video", monthly_limit=100, daily_limit=20, priority=2),
            ServiceAllocation("3d", monthly_limit=50, daily_limit=10, priority=1),
        ],
        features=[
            "Everything in Pro",
            "Custom model fine-tuning",
            "Team management",
            "Advanced analytics",
            "Priority support",
            "SLA guarantee",
            "Custom integrations",
            "White-label options",
        ],
        max_concurrent=20,
        support_level="priority",
        api_access=True,
        webhook_access=True,
        custom_models=True,
        sla_uptime=99.9,
    ),

    PlanTier.ENTERPRISE: SubscriptionPlan(
        id="enterprise",
        name="Enterprise",
        tier=PlanTier.ENTERPRISE,
        price_monthly=499.99,
        price_yearly=4999.99,
        credits_monthly=100000,
        credits_per_dollar=500,
        services=[
            ServiceAllocation("text", monthly_limit=50000, daily_limit=5000, max_tokens_per_request=16384, rate_limit_per_minute=1000, priority=3),
            ServiceAllocation("image", monthly_limit=10000, daily_limit=1000, rate_limit_per_minute=200, priority=2),
            ServiceAllocation("video", monthly_limit=500, daily_limit=50, priority=3),
            ServiceAllocation("3d", monthly_limit=200, daily_limit=30, priority=2),
        ],
        features=[
            "Everything in Business",
            "Dedicated infrastructure",
            "Custom SLA",
            "Account manager",
            "On-premise option",
            "Advanced security",
            "Audit logs",
            "Invoice billing",
        ],
        max_concurrent=100,
        support_level="dedicated",
        api_access=True,
        webhook_access=True,
        custom_models=True,
        sla_uptime=99.99,
    ),
}


def get_plan(tier: PlanTier) -> SubscriptionPlan:
    """Get plan by tier."""
    return plans[tier]


def get_plan_by_id(plan_id: str) -> Optional[SubscriptionPlan]:
    """Get plan by string ID."""
    for tier, plan in plans.items():
        if plan.id == plan_id:
            return plan
    return None


def list_plans() -> List[dict]:
    """List all plans as dicts."""
    return [
        {
            "id": p.id,
            "name": p.name,
            "tier": p.tier.value,
            "price_monthly": p.price_monthly,
            "price_yearly": p.price_yearly,
            "credits_monthly": p.credits_monthly,
            "features": p.features,
            "popular": p.tier == PlanTier.PRO,
        }
        for p in plans.values()
    ]