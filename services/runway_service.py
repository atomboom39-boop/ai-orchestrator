"""Runway ML service for video generation."""

import os
from typing import Optional
from .base import BaseService


class RunwayService(BaseService):
    """Runway ML API integration for video generation."""

    BASE_URL = "https://api.dev.runwayml.com/v1"

    def __init__(self):
        api_key = os.getenv("RUNWAY_API_KEY")
        super().__init__(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        duration: str = "5s",
    ) -> dict:
        """Generate video using Runway ML."""
        if not self.api_key:
            return {
                "error": "Runway API key not configured",
                "video_url": "",
                "service": "runway",
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-09-13",
        }

        # Build the task
        task_payload = {
            "promptText": prompt,
            "duration": int(duration.replace("s", "")),
        }

        if image_url:
            task_payload["image_url"] = image_url
            task_type = "image_to_video"
        else:
            task_type = "text_to_video"

        # Create generation task
        response = await self._make_request(
            method="POST",
            url=f"{self.BASE_URL}/image_to_video",
            headers=headers,
            json=task_payload,
        )

        data = response.json()
        task_id = data.get("id")

        return {
            "task_id": task_id,
            "status": "processing",
            "message": f"Video generation started. Task ID: {task_id}",
            "service": "runway",
            "check_status": f"/status/runway/{task_id}",
        }

    async def check_status(self, task_id: str) -> dict:
        """Check video generation status."""
        if not self.api_key:
            return {"error": "Runway API key not configured"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        response = await self._make_request(
            method="GET",
            url=f"{self.BASE_URL}/tasks/{task_id}",
            headers=headers,
        )

        data = response.json()
        return {
            "task_id": task_id,
            "status": data.get("status"),
            "video_url": data.get("output", {}).get("video_url"),
            "progress": data.get("progress"),
        }

    async def health_check(self) -> bool:
        """Check if Runway API is accessible."""
        # Runway API key is configured — assume available
        # (health endpoint not reliably documented)
        return bool(self.api_key)
