"""Real-time service monitoring."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Result of a health check."""
    service: str
    status: HealthStatus
    latency_ms: float
    timestamp: datetime
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class ServiceMonitor:
    """Monitor service health and performance."""

    def __init__(self):
        self._health_history: Dict[str, List[HealthCheck]] = {}
        self._alert_callbacks: List[Callable] = []
        self._thresholds = {
            "latency_warn_ms": 1000,
            "latency_critical_ms": 5000,
            "error_rate_warn": 0.1,  # 10%
            "error_rate_critical": 0.3,  # 30%
        }
        self._running = False

    async def check_health(self, service_id: str,
                            health_func: Callable) -> HealthCheck:
        """Run a health check for a service."""
        start = time.time()
        try:
            result = await health_func()
            latency = (time.time() - start) * 1000

            if latency > self._thresholds["latency_critical_ms"]:
                status = HealthStatus.UNHEALTHY
            elif latency > self._thresholds["latency_warn_ms"]:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY

            check = HealthCheck(
                service=service_id,
                status=status,
                latency_ms=latency,
                timestamp=datetime.now(),
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            check = HealthCheck(
                service=service_id,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                timestamp=datetime.now(),
                error=str(e),
            )

        # Store in history
        if service_id not in self._health_history:
            self._health_history[service_id] = []
        self._health_history[service_id].append(check)

        # Keep last 1000 checks per service
        if len(self._health_history[service_id]) > 1000:
            self._health_history[service_id] = self._health_history[service_id][-1000:]

        # Check alerts
        if status in (HealthStatus.UNHEALTHY, HealthStatus.DEGRADED):
            await self._trigger_alerts(check)

        return check

    def get_service_status(self, service_id: str) -> dict:
        """Get current status and history for a service."""
        history = self._health_history.get(service_id, [])
        if not history:
            return {"service": service_id, "status": HealthStatus.UNKNOWN.value}

        recent = history[-10:]  # Last 10 checks
        avg_latency = sum(h.latency_ms for h in recent) / len(recent)
        error_count = sum(1 for h in recent if h.status == HealthStatus.UNHEALTHY)
        error_rate = error_count / len(recent)

        current = history[-1]

        return {
            "service": service_id,
            "status": current.status.value,
            "latency_ms": current.latency_ms,
            "avg_latency_ms": round(avg_latency, 2),
            "error_rate": round(error_rate, 4),
            "last_check": current.timestamp.isoformat(),
            "error": current.error,
            "checks_count": len(history),
        }

    def get_all_services_status(self) -> dict:
        """Get status of all monitored services."""
        return {
            service_id: self.get_service_status(service_id)
            for service_id in self._health_history
        }

    def register_alert(self, callback: Callable):
        """Register an alert callback."""
        self._alert_callbacks.append(callback)

    async def _trigger_alerts(self, check: HealthCheck):
        """Trigger alert callbacks."""
        for callback in self._alert_callbacks:
            try:
                await callback(check)
            except Exception:
                pass

    def set_thresholds(self, **kwargs):
        """Update monitoring thresholds."""
        self._thresholds.update(kwargs)

    def get_uptime(self, service_id: str, hours: int = 24) -> float:
        """Calculate uptime percentage for a service."""
        history = self._health_history.get(service_id, [])
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [h for h in history if h.timestamp > cutoff]

        if not recent:
            return 100.0

        healthy = sum(1 for h in recent if h.status == HealthStatus.HEALTHY)
        return round((healthy / len(recent)) * 100, 2)


# Global monitor instance
monitor = ServiceMonitor()