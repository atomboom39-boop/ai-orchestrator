"""Cost optimization and budget management."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class BudgetAlert:
    """Budget alert."""
    level: AlertLevel
    message: str
    current_usage: float
    budget_limit: float
    percentage: float


class CostOptimizer:
    """Optimize costs across AI services."""

    # Cost per 1000 tokens (approximate)
    SERVICE_COSTS = {
        "groq": {
            "openai/gpt-oss-120b": 0.59,
            "openai/gpt-oss-20b": 0.20,
            "qwen/qwen3.8-27b": 0.27,
            "allam-2-7b": 0.05,
        },
        "openai": {
            "gpt-4": 30.0,
            "gpt-4-turbo": 10.0,
            "gpt-3.5-turbo": 0.5,
        },
        "replicate": {
            "stable-diffusion": 0.005,  # per image
        },
        "runway": {
            "video": 0.10,  # per second
        },
        "luma": {
            "3d": 0.50,  # per generation
        },
    }

    def __init__(self):
        self._budgets: Dict[str, float] = {}
        self._usage: Dict[str, Dict[str, float]] = {}
        self._alerts: List[BudgetAlert] = []
        self._alert_thresholds = {
            "warning": 0.7,  # 70%
            "critical": 0.9,  # 90%
        }

    def set_budget(self, user_id: str, amount: float):
        """Set budget limit for a user."""
        self._budgets[user_id] = amount

    def get_budget(self, user_id: str) -> float:
        """Get budget limit for a user."""
        return self._budgets.get(user_id, 0)

    def record_usage(self, user_id: str, service: str, model: str,
                      tokens: int = 0, seconds: float = 0, images: int = 0):
        """Record usage for cost tracking."""
        if user_id not in self._usage:
            self._usage[user_id] = {
                "total_cost": 0.0,
                "by_service": {},
                "by_model": {},
                "history": [],
            }

        usage = self._usage[user_id]
        cost = self._calculate_cost(service, model, tokens, seconds, images)

        usage["total_cost"] += cost
        usage["by_service"][service] = usage["by_service"].get(service, 0) + cost
        usage["by_model"][f"{service}/{model}"] = usage["by_model"].get(f"{service}/{model}", 0) + cost
        usage["history"].append({
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "model": model,
            "tokens": tokens,
            "seconds": seconds,
            "images": images,
            "cost": cost,
        })

        # Check budget alerts
        self._check_alerts(user_id)

        return cost

    def _calculate_cost(self, service: str, model: str,
                         tokens: int, seconds: float, images: int) -> float:
        """Calculate cost for a request."""
        service_costs = self.SERVICE_COSTS.get(service, {})
        base_cost = service_costs.get(model, 0)

        if service in ("groq", "openai"):
            return (tokens / 1000) * base_cost
        elif service == "runway":
            return seconds * base_cost
        elif service in ("replicate", "luma"):
            return images * base_cost

        return 0.0

    def _check_alerts(self, user_id: str):
        """Check if budget alerts should be triggered."""
        budget = self._budgets.get(user_id)
        if not budget:
            return

        usage = self._usage.get(user_id, {}).get("total_cost", 0)
        percentage = usage / budget if budget > 0 else 0

        if percentage >= self._alert_thresholds["critical"]:
            self._alerts.append(BudgetAlert(
                level=AlertLevel.CRITICAL,
                message=f"Budget usage at {percentage*100:.1f}% - approaching limit!",
                current_usage=usage,
                budget_limit=budget,
                percentage=percentage,
            ))
        elif percentage >= self._alert_thresholds["warning"]:
            self._alerts.append(BudgetAlert(
                level=AlertLevel.WARNING,
                message=f"Budget usage at {percentage*100:.1f}%",
                current_usage=usage,
                budget_limit=budget,
                percentage=percentage,
            ))

    def check_budget(self, user_id: str) -> dict:
        """Check current budget status."""
        budget = self._budgets.get(user_id, 0)
        usage_data = self._usage.get(user_id, {})
        usage = usage_data.get("total_cost", 0)

        return {
            "budget": budget,
            "usage": usage,
            "remaining": max(0, budget - usage),
            "percentage": (usage / budget * 100) if budget > 0 else 0,
            "alerts": [
                {"level": a.level.value, "message": a.message}
                for a in self._alerts[-5:]  # Last 5 alerts
            ],
        }

    def get_usage_report(self, user_id: str, days: int = 30) -> dict:
        """Generate usage report."""
        usage = self._usage.get(user_id, {})
        history = usage.get("history", [])

        cutoff = datetime.now() - timedelta(days=days)
        recent_history = [
            h for h in history
            if datetime.fromisoformat(h["timestamp"]) > cutoff
        ]

        # Aggregate by service
        by_service = {}
        for h in recent_history:
            svc = h["service"]
            by_service[svc] = by_service.get(svc, 0) + h["cost"]

        # Aggregate by day
        by_day = {}
        for h in recent_history:
            day = h["timestamp"][:10]
            by_day[day] = by_day.get(day, 0) + h["cost"]

        total_cost = sum(h["cost"] for h in recent_history)
        total_tokens = sum(h.get("tokens", 0) for h in recent_history)

        return {
            "period_days": days,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "avg_daily_cost": total_cost / max(len(by_day), 1),
            "by_service": by_service,
            "by_day": by_day,
            "top_models": sorted(
                usage.get("by_model", {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "request_count": len(recent_history),
        }

    def suggest_optimization(self, user_id: str) -> List[str]:
        """Suggest cost optimizations based on usage patterns."""
        usage = self._usage.get(user_id, {})
        suggestions = []

        # Check if using expensive models
        by_model = usage.get("by_model", {})
        for model, cost in by_model.items():
            if "gpt-4" in model and cost > 10:
                suggestions.append(
                    f"Consider using GPT-3.5-turbo instead of {model} for simpler tasks"
                )
            if "llama-3.3-70b" in model:
                suggestions.append(
                    f"Consider allam-2-7b for faster, cheaper inference"
                )

        # Check daily costs
        history = usage.get("history", [])
        if len(history) > 10:
            recent_costs = [h["cost"] for h in history[-10:]]
            avg_recent = sum(recent_costs) / len(recent_costs)
            if avg_recent > 5:
                suggestions.append(
                    f"Average recent cost is ${avg_recent:.2f}/request. "
                    "Consider using caching for repeated queries."
                )

        # General suggestions
        if not suggestions:
            suggestions.append("Usage looks efficient! Keep up the good work.")

        return suggestions

    def get_cheapest_service(self, service_type: str) -> str:
        """Get the cheapest service for a given type."""
        cost_map = {
            "text": ("groq", "allam-2-7b"),
            "image": ("replicate", "stable-diffusion"),
            "video": ("runway", "video"),
            "3d": ("luma", "3d"),
        }
        return cost_map.get(service_type, ("unknown", "unknown"))[0]

    def compare_services(self) -> dict:
        """Compare costs across all services."""
        return self.SERVICE_COSTS


# Global optimizer instance
optimizer = CostOptimizer()
