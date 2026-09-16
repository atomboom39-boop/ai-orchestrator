"""Luma AI service for 3D model generation."""

import os
from typing import Optional
from .base import BaseService


class LumaService(BaseService):
    """Luma AI API integration for 3D generation."""

    BASE_URL = "https://api.lumalabs.ai/dream-machine/v1"

    def __init__(self):
        api_key = os.getenv("LUMA_API_KEY")
        super().__init__(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        image_url: Optional[str] = None,
    ) -> dict:
        """Generate 3D model using Luma AI."""
        if not self.api_key:
            return {
                "error": "Luma API key not configured",
                "model_url": "",
                "service": "luma",
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
        }

        if image_url:
            payload["image_url"] = image_url

        response = await self._make_request(
            method="POST",
            url=f"{self.BASE_URL}/generations",
            headers=headers,
            json=payload,
        )

        data = response.json()
        generation_id = data.get("id")

        return {
            "generation_id": generation_id,
            "status": data.get("status", "processing"),
            "message": f"3D generation started. ID: {generation_id}",
            "service": "luma",
            "check_status": f"/status/luma/{generation_id}",
        }

    async def check_status(self, generation_id: str) -> dict:
        """Check 3D generation status."""
        if not self.api_key:
            return {"error": "Luma API key not configured"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        response = await self._make_request(
            method="GET",
            url=f"{self.BASE_URL}/generations/{generation_id}",
            headers=headers,
        )

        data = response.json()
        assets = data.get("assets", {})

        return {
            "generation_id": generation_id,
            "status": data.get("status"),
            "model_url": assets.get("model"),
            "thumbnail_url": assets.get("thumbnail"),
            "progress": data.get("progress"),
        }

    async def health_check(self) -> bool:
        """Check if Luma API is accessible."""
        # Luma API key is configured — assume available
        # (will verify on first generation request)
        return bool(self.api_key)
