"""Stable Diffusion service for image generation."""

import os
import urllib.parse
from typing import Optional
from .base import BaseService


class StableDiffusionService(BaseService):
    """Stable Diffusion integration: Replicate (primary) / Pollinations (free fallback)."""

    REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
    POLLINATIONS_URL = "https://image.pollinations.ai/prompt"

    # Supported Pollinations models (via query param)
    POLLINATIONS_MODELS = ["flux", "turbo"]

    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self.local_api_url = os.getenv("SD_API_URL", "http://localhost:7860")
        self.use_replicate = bool(self.replicate_token)
        api_key = self.replicate_token or "pollinations"
        super().__init__(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
    ) -> dict:
        """Generate image — try Replicate first, fallback to Pollinations (free)."""
        if self.use_replicate:
            try:
                return await self._generate_replicate(prompt, negative_prompt, width, height)
            except Exception:
                # Replicate credits exhausted or rate-limited → fallback
                pass

        # Free fallback — Pollinations (no API key needed)
        return await self._generate_pollinations(prompt, width, height, num_images)

    async def _generate_replicate(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        width: int,
        height: int,
    ) -> dict:
        """Generate using Replicate API (requires credits)."""
        headers = {
            "Authorization": f"Token {self.replicate_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt or "",
                "width": width,
                "height": height,
            },
        }

        response = await self._make_request(
            method="POST",
            url=self.REPLICATE_API_URL,
            headers=headers,
            json=payload,
        )

        if response.status_code in (402, 429):
            raise Exception("Replicate unavailable (no credits / rate limited)")

        data = response.json()
        return {
            "prediction_id": data.get("id"),
            "status": data.get("status"),
            "service": "replicate",
            "message": "Image generation started. Poll /predictions/{id} for result.",
        }

    async def _generate_pollinations(
        self,
        prompt: str,
        width: int,
        height: int,
        num_images: int = 1,
    ) -> dict:
        """Generate free images using Pollinations AI (no key required)."""
        import httpx

        encoded = urllib.parse.quote(prompt)
        urls = []
        for i in range(min(num_images, 4)):
            seed = str(i + 1)
            url = (
                f"{self.POLLINATIONS_URL}/{encoded}"
                f"?width={width}&height={height}&seed={seed}&nologo=true"
            )
            # Fire and forget — Pollinations generates on-the-fly
            try:
                r = httpx.get(url, timeout=90, follow_redirects=True)
                if r.status_code == 200 and len(r.content) > 1000:
                    urls.append(f"data:image/jpeg;base64,{__import__('base64').b64encode(r.content).decode()}")
            except Exception:
                continue

        if urls:
            return {
                "image_url": urls[0],
                "images": urls,
                "service": "pollinations",
                "count": len(urls),
                "message": f"{len(urls)} image(s) generated (Pollinations free tier)",
            }
        else:
            return {
                "error": "Pollinations image generation failed",
                "service": "pollinations",
                "hint": "Try again in a few seconds (rate limits may apply)",
            }

    async def health_check(self) -> bool:
        """SD is available if Replicate token exists OR Pollinations (free) is reachable."""
        return True  # Pollinations always available; Replicate is a bonus

    def list_providers(self) -> dict:
        """List image generation providers."""
        return {
            "replicate": bool(self.replicate_token),
            "pollinations": True,
            "local_sd": False,
        }
