"""Base service class with common functionality."""

import httpx
from abc import ABC, abstractmethod
from typing import Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential


class BaseService(ABC):
    """Base class for all AI service integrations."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)

    @abstractmethod
    async def generate(self, **kwargs) -> Any:
        """Generate output from the service."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is available."""
        pass

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic."""
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            data=data,
        )
        response.raise_for_status()
        return response

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
