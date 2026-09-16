"""Analytics tracker for usage and performance metrics."""

import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
from collections import defaultdict


class AnalyticsTracker:
    """Track usage, performance, and costs."""

    def __init__(self):
        self._events: List[dict] = []
        self._counters: Dict[str, int] = defaultdict(int)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._service_stats: Dict[str, dict] = defaultdict(lambda: {
            "requests": 0,
            "success": 0,
            "failures": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "latencies": [],
        })

    def track_event(self, event_type: str, service: str = None,
                     user_id: str = None, metadata: dict = None):
        """Track an analytics event."""
        event = {
            "type": event_type,
            "service": service,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        self._events.append(event)
        self._counters[event_type] += 1

        if service:
            self._counters[f"{service}.{event_type}"] += 1

    def track_generation(self, service: str, user_id: str = None,
                          tokens: int = 0, cost: float = 0.0,
                          latency_ms: float = 0, success: bool = True):
        """Track a generation event."""
        stats = self._service_stats[service]
        stats["requests"] += 1
        if success:
            stats["success"] += 1
        else:
            stats["failures"] += 1
        stats["total_tokens"] += tokens
        stats["total_cost"] += cost
        if latency_ms > 0:
            stats["latencies"].append(latency_ms)
            # Keep last 1000 latencies
            if len(stats["latencies"]) > 1000:
                stats["latencies"] = stats["latencies"][-1000:]

        self.track_event("generation", service, user_id, {
            "tokens": tokens,
            "cost": cost,
            "latency_ms": latency_ms,
            "success": success,
        })

    def track_request(self, endpoint: str, method: str = "POST",
                       status_code: int = 200, latency_ms: float = 0):
        """Track an HTTP request."""
        self.track_event("request", metadata={
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "latency_ms": latency_ms,
        })

    def get_service_stats(self, service: str = None) -> dict:
        """Get statistics for a service or all services."""
        if service:
            stats = self._service_stats.get(service, {})
            if stats.get("latencies"):
                sorted_lat = sorted(stats["latencies"])
                stats["p50_latency"] = sorted_lat[len(sorted_lat) // 2]
                stats["p95_latency"] = sorted_lat[int(len(sorted_lat) * 0.95)]
                stats["p99_latency"] = sorted_lat[int(len(sorted_lat) * 0.99)]
                stats["avg_latency"] = sum(sorted_lat) / len(sorted_lat)
            return stats

        return dict(self._service_stats)

    def get_dashboard(self, hours: int = 24) -> dict:
        """Get dashboard metrics."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_events = [
            e for e in self._events
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

        # Count by service
        service_counts = defaultdict(int)
        total_cost = 0.0
        total_tokens = 0
        for event in recent_events:
            if event["service"]:
                service_counts[event["service"]] += 1
            meta = event.get("metadata", {})
            total_cost += meta.get("cost", 0)
            total_tokens += meta.get("tokens", 0)

        return {
            "period_hours": hours,
            "total_events": len(recent_events),
            "events_by_service": dict(service_counts),
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "service_stats": self.get_service_stats(),
            "top_endpoints": self._get_top_endpoints(recent_events),
        }

    def _get_top_endpoints(self, events: List[dict], limit: int = 10) -> List[dict]:
        """Get most used endpoints."""
        endpoint_counts = defaultdict(int)
        for event in events:
            if event["type"] == "request":
                endpoint = event.get("metadata", {}).get("endpoint", "unknown")
                endpoint_counts[endpoint] += 1

        sorted_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"endpoint": ep, "count": cnt} for ep, cnt in sorted_endpoints[:limit]]

    def get_counters(self, prefix: str = None) -> dict:
        """Get event counters."""
        if prefix:
            return {k: v for k, v in self._counters.items() if k.startswith(prefix)}
        return dict(self._counters)

    def reset(self):
        """Reset all analytics data."""
        self._events.clear()
        self._counters.clear()
        self._timers.clear()
        self._service_stats.clear()


# Timer decorator for tracking latency
def track_latency(service: str = None):
    """Decorator to track function execution latency."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                latency = (time.time() - start) * 1000
                tracker.track_event(f"{func.__name__}.success", service or "system", metadata={
                    "latency_ms": latency,
                })
                return result
            except Exception as e:
                latency = (time.time() - start) * 1000
                tracker.track_event(f"{func.__name__}.error", service or "system", metadata={
                    "latency_ms": latency,
                    "error": str(e),
                })
                raise
        return wrapper
    return decorator


# Global tracker instance
tracker = AnalyticsTracker()