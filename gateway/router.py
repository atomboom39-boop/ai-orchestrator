"""Smart router - picks the best service for each request."""

import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ServiceType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    THREE_D = "3d"
    AUDIO = "audio"


@dataclass
class RoutingRule:
    """A routing rule for service selection."""
    service_type: ServiceType
    service_id: str
    priority: int = 0  # Higher = preferred
    conditions: dict = None  # Optional conditions
    max_tokens: int = None
    cost_per_1k: float = 0.0


class SmartRouter:
    """Intelligent request router with load balancing and cost optimization."""

    def __init__(self):
        self._rules: Dict[ServiceType, List[RoutingRule]] = {}
        self._service_health: Dict[str, float] = {}  # service -> health score (0-1)
        self._service_load: Dict[str, int] = {}  # service -> current load
        self._strategy = "balanced"  # balanced, cost, speed, quality

    def register_service(self, service_type: ServiceType, service_id: str,
                          priority: int = 0, cost_per_1k: float = 0.0,
                          max_tokens: int = None, conditions: dict = None):
        """Register a service for routing."""
        if service_type not in self._rules:
            self._rules[service_type] = []

        rule = RoutingRule(
            service_type=service_type,
            service_id=service_id,
            priority=priority,
            conditions=conditions,
            max_tokens=max_tokens,
            cost_per_1k=cost_per_1k,
        )
        self._rules[service_type].append(rule)
        self._service_health[service_id] = 1.0
        self._service_load[service_id] = 0

    def set_strategy(self, strategy: str):
        """Set routing strategy: balanced, cost, speed, quality."""
        self._strategy = strategy

    def route(self, service_type: ServiceType, request: dict = None) -> Optional[str]:
        """Route a request to the best service."""
        rules = self._rules.get(service_type, [])
        if not rules:
            return None

        request = request or {}

        # Score each service
        scored = []
        for rule in rules:
            score = self._calculate_score(rule, request)
            scored.append((score, rule.service_id))

        if not scored:
            return None

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def _calculate_score(self, rule: RoutingRule, request: dict) -> float:
        """Calculate routing score for a service."""
        score = rule.priority * 10  # Base score from priority

        # Health factor
        health = self._service_health.get(rule.service_id, 0.5)
        score *= health

        # Load factor (prefer less loaded services)
        load = self._service_load.get(rule.service_id, 0)
        load_penalty = min(load / 10, 0.5)  # Up to 50% penalty
        score *= (1 - load_penalty)

        # Strategy adjustments
        if self._strategy == "cost":
            if rule.cost_per_1k > 0:
                score *= (1 / (rule.cost_per_1k + 0.01))
        elif self._strategy == "speed":
            # Prefer lower-priority (usually faster) services
            score = 100 - rule.priority + health * 50
        elif self._strategy == "quality":
            score *= rule.priority  # Strongly prefer higher priority

        # Check conditions
        if rule.conditions:
            for key, value in rule.conditions.items():
                if key == "max_tokens" and request.get("max_tokens", 0) > value:
                    score *= 0.1  # Heavily penalize if over limit
                elif key == "language":
                    if request.get("language") not in (value if isinstance(value, list) else [value]):
                        score *= 0.5

        return score

    def update_health(self, service_id: str, score: float):
        """Update service health score (0-1)."""
        self._service_health[service_id] = max(0.0, min(1.0, score))

    def increment_load(self, service_id: str):
        """Increment service load counter."""
        self._service_load[service_id] = self._service_load.get(service_id, 0) + 1

    def decrement_load(self, service_id: str):
        """Decrement service load counter."""
        self._service_load[service_id] = max(0, self._service_load.get(service_id, 0) - 1)

    def get_routing_table(self) -> dict:
        """Get the current routing configuration."""
        result = {}
        for service_type, rules in self._rules.items():
            result[service_type.value] = [
                {
                    "service_id": r.service_id,
                    "priority": r.priority,
                    "cost_per_1k": r.cost_per_1k,
                    "health": self._service_health.get(r.service_id, 0),
                    "load": self._service_load.get(r.service_id, 0),
                }
                for r in rules
            ]
        return result

    def get_recommendation(self, service_type: ServiceType) -> dict:
        """Get detailed routing recommendation."""
        rules = self._rules.get(service_type, [])
        if not rules:
            return {"service": None, "reason": "No services registered"}

        scored = [(self._calculate_score(r, {}), r) for r in rules]
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, best_rule = scored[0]

        return {
            "service": best_rule.service_id,
            "score": best_score,
            "strategy": self._strategy,
            "alternatives": [
                {"service": r.service_id, "score": s}
                for s, r in scored[1:3]  # Top 2 alternatives
            ],
        }


# Global router instance
router = SmartRouter()
