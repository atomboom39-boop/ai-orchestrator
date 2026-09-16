"""API Gateway middleware - rate limiting, auth, logging."""

import time
import hashlib
import secrets
from typing import Dict, Optional, Callable
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self):
        self._buckets: Dict[str, dict] = {}
        self._default_rate = 100  # requests per minute
        self._default_burst = 20  # max burst

    def _get_bucket(self, key: str) -> dict:
        if key not in self._buckets:
            self._buckets[key] = {
                "tokens": self._default_burst,
                "last_refill": time.time(),
                "rate": self._default_rate,
                "burst": self._default_burst,
            }
        return self._buckets[key]

    def configure(self, key: str, rate: int = None, burst: int = None):
        """Configure rate limits for a key."""
        bucket = self._get_bucket(key)
        if rate:
            bucket["rate"] = rate
        if burst:
            bucket["burst"] = burst

    def allow(self, key: str) -> bool:
        """Check if request is allowed."""
        bucket = self._get_bucket(key)

        # Refill tokens
        now = time.time()
        elapsed = now - bucket["last_refill"]
        tokens_to_add = elapsed * (bucket["rate"] / 60)  # per second
        bucket["tokens"] = min(bucket["burst"], bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = now

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        return False

    def get_remaining(self, key: str) -> int:
        """Get remaining tokens for a key."""
        bucket = self._get_bucket(key)
        return int(bucket["tokens"])


class AuthMiddleware:
    """API key authentication."""

    def __init__(self):
        self._api_keys: Dict[str, dict] = {}
        self._master_key = secrets.token_hex(32)

    def generate_key(self, user_id: str, name: str = None) -> str:
        """Generate a new API key for a user."""
        key = f"sk-{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        self._api_keys[key_hash] = {
            "user_id": user_id,
            "name": name or f"key-{len(self._api_keys)}",
            "created_at": datetime.now(),
            "is_active": True,
            "permissions": ["generate", "read"],
        }

        return key

    def validate_key(self, api_key: str) -> Optional[dict]:
        """Validate an API key and return its info."""
        if not api_key:
            return None

        # Check master key
        if api_key == self._master_key:
            return {"user_id": "master", "permissions": ["admin", "generate", "read", "manage"]}

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_info = self._api_keys.get(key_hash)

        if key_info and key_info["is_active"]:
            return key_info
        return None

    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if key_hash in self._api_keys:
            self._api_keys[key_hash]["is_active"] = False
            return True
        return False

    def list_keys(self, user_id: str = None) -> list:
        """List API keys, optionally filtered by user."""
        result = []
        for key_hash, info in self._api_keys.items():
            if user_id and info["user_id"] != user_id:
                continue
            result.append({
                "name": info["name"],
                "user_id": info["user_id"],
                "created_at": info["created_at"].isoformat(),
                "is_active": info["is_active"],
            })
        return result


class RequestLogger:
    """Log all API requests."""

    def __init__(self):
        self._logs: list = []
        self._max_logs = 10000

    def log(self, request: Request, response_code: int,
             user_id: str = None, service: str = None,
             latency_ms: float = 0):
        """Log a request."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.query_params),
            "response_code": response_code,
            "user_id": user_id,
            "service": service,
            "latency_ms": latency_ms,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        self._logs.append(entry)

        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]

    def get_logs(self, limit: int = 100, user_id: str = None,
                  status_code: int = None) -> list:
        """Get recent logs."""
        logs = self._logs

        if user_id:
            logs = [l for l in logs if l.get("user_id") == user_id]
        if status_code:
            logs = [l for l in logs if l.get("response_code") == status_code]

        return logs[-limit:]

    def get_stats(self, hours: int = 24) -> dict:
        """Get request statistics."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            l for l in self._logs
            if datetime.fromisoformat(l["timestamp"]) > cutoff
        ]

        status_counts = defaultdict(int)
        path_counts = defaultdict(int)
        total_latency = 0

        for log in recent:
            status_counts[str(log["response_code"])] += 1
            path_counts[log["path"]] += 1
            total_latency += log.get("latency_ms", 0)

        return {
            "total_requests": len(recent),
            "status_codes": dict(status_counts),
            "top_paths": dict(sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "avg_latency_ms": round(total_latency / max(len(recent), 1), 2),
        }
