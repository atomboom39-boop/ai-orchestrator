"""Groq service for fast text generation."""

import os
from typing import Optional
from .base import BaseService


class GroqService(BaseService):
    """Groq API integration for ultra-fast text generation."""

    BASE_URL = "https://api.groq.com/openai/v1"

    MODELS = {
        "openai/gpt-oss-120b": "GPT-OSS 120B (best quality)",
        "openai/gpt-oss-20b": "GPT-OSS 20B (fast)",
        "qwen/qwen3.8-27b": "Qwen 3.8 27B (balanced)",
        "allam-2-7b": "ALLam 2 7B (cheapest)",
    }

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        super().__init__(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        model: str = "openai/gpt-oss-120b",
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> dict:
        """Generate text using Groq."""
        if not self.api_key:
            return {
                "error": "Groq API key not configured",
                "text": "",
                "model": model,
                "tokens_used": 0,
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # gpt-oss models are reasoning models; hide reasoning so the
        # answer lands in `content` instead of being eaten up by reasoning.
        if model.startswith("openai/gpt-oss-"):
            payload["reasoning_format"] = "hidden"

        response = await self._make_request(
            method="POST",
            url=f"{self.BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )

        data = response.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return {
            "text": choice["message"]["content"],
            "model": model,
            "tokens_used": usage.get("total_tokens", 0),
            "finish_reason": choice.get("finish_reason", "stop"),
        }

    async def health_check(self) -> bool:
        """Check if Groq API is accessible."""
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self._make_request(
                method="GET",
                url=f"{self.BASE_URL}/models",
                headers=headers,
            )
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> dict:
        """List available Groq models."""
        return self.MODELS
