"""Credit management system."""

from typing import Optional, Dict
from datetime import datetime, timedelta
from enum import Enum


class CreditType(str, Enum):
    SUBSCRIPTION = "subscription"  # Monthly plan credits
    PURCHASED = "purchased"  # Bought extra credits
    BONUS = "bonus"  # Promotional credits
    REFUND = "refund"  # Refunded credits


class CreditManager:
    """Manage user credits."""

    def __init__(self):
        self._credits: Dict[str, dict] = {}  # user_id -> credit info

    def initialize_user(self, user_id: str, plan_credits: int = 100):
        """Initialize user credits."""
        if user_id not in self._credits:
            self._credits[user_id] = {
                "total": plan_credits,
                "used": 0,
                "remaining": plan_credits,
                "breakdown": {
                    CreditType.SUBSCRIPTION.value: plan_credits,
                    CreditType.PURCHASED.value: 0,
                    CreditType.BONUS.value: 0,
                },
                "history": [],
                "reset_date": (datetime.now() + timedelta(days=30)).isoformat(),
            }

    def get_balance(self, user_id: str) -> dict:
        """Get user's credit balance."""
        if user_id not in self._credits:
            self.initialize_user(user_id)

        credits = self._credits[user_id]

        # Check if reset needed
        reset_date = datetime.fromisoformat(credits["reset_date"])
        if datetime.now() > reset_date:
            self._reset_monthly(user_id)
            credits = self._credits[user_id]

        return {
            "total": credits["total"],
            "used": credits["used"],
            "remaining": credits["remaining"],
            "breakdown": credits["breakdown"],
            "reset_date": credits["reset_date"],
        }

    def use_credits(self, user_id: str, amount: int,
                     service: str = None) -> dict:
        """Deduct credits for a request."""
        if user_id not in self._credits:
            self.initialize_user(user_id)

        credits = self._credits[user_id]

        if credits["remaining"] < amount:
            return {
                "success": False,
                "error": "Insufficient credits",
                "remaining": credits["remaining"],
                "required": amount,
            }

        credits["remaining"] -= amount
        credits["used"] += amount

        # Record in history
        credits["history"].append({
            "timestamp": datetime.now().isoformat(),
            "amount": -amount,
            "service": service,
            "balance_after": credits["remaining"],
        })

        return {
            "success": True,
            "deducted": amount,
            "remaining": credits["remaining"],
        }

    def add_credits(self, user_id: str, amount: int,
                     credit_type: CreditType = CreditType.PURCHASED,
                     description: str = None) -> dict:
        """Add credits to user account."""
        if user_id not in self._credits:
            self.initialize_user(user_id)

        credits = self._credits[user_id]
        credits["total"] += amount
        credits["remaining"] += amount
        credits["breakdown"][credit_type.value] += amount

        credits["history"].append({
            "timestamp": datetime.now().isoformat(),
            "amount": amount,
            "type": credit_type.value,
            "description": description,
            "balance_after": credits["remaining"],
        })

        return {
            "success": True,
            "added": amount,
            "type": credit_type.value,
            "total": credits["total"],
            "remaining": credits["remaining"],
        }

    def _reset_monthly(self, user_id: str):
        """Reset monthly subscription credits."""
        credits = self._credits[user_id]

        # Keep purchased/bonus credits
        purchased = credits["breakdown"].get(CreditType.PURCHASED.value, 0)
        bonus = credits["breakdown"].get(CreditType.BONUS.value, 0)

        # Reset to plan allocation (would need plan info here)
        plan_credits = 100  # Default, should come from user's plan

        credits["total"] = plan_credits + purchased + bonus
        credits["used"] = 0
        credits["remaining"] = credits["total"]
        credits["breakdown"] = {
            CreditType.SUBSCRIPTION.value: plan_credits,
            CreditType.PURCHASED.value: purchased,
            CreditType.BONUS.value: bonus,
        }
        credits["reset_date"] = (datetime.now() + timedelta(days=30)).isoformat()

        credits["history"].append({
            "timestamp": datetime.now().isoformat(),
            "amount": plan_credits,
            "type": "monthly_reset",
            "balance_after": credits["remaining"],
        })

    def get_usage_history(self, user_id: str, limit: int = 50) -> list:
        """Get credit usage history."""
        if user_id not in self._credits:
            return []

        return self._credits[user_id]["history"][-limit:]

    def estimate_cost(self, service: str, model: str = None,
                       tokens: int = 0) -> dict:
        """Estimate credit cost for a request."""
        # Credit costs (simplified)
        costs = {
            "text": {"base": 1, "per_1k_tokens": 0.5},
            "image": {"base": 5, "per_1k_tokens": 0},
            "video": {"base": 50, "per_1k_tokens": 0},
            "3d": {"base": 25, "per_1k_tokens": 0},
        }

        service_cost = costs.get(service, costs["text"])
        total = service_cost["base"] + (tokens / 1000 * service_cost["per_1k_tokens"])

        return {
            "service": service,
            "estimated_credits": max(1, int(total)),
            "breakdown": service_cost,
        }


# Global instance
credit_manager = CreditManager()