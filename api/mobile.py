"""
Mobile API - Optimized endpoints for mobile apps.
Features: lightweight responses, pagination, image compression.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/mobile", tags=["mobile"])


class MobileTextRequest(BaseModel):
    """Simplified text request for mobile."""
    prompt: str
    model: Optional[str] = "qwen/qwen3.8-27b"  # Fast model default
    max_tokens: int = Field(default=512, le=2048)


class MobileImageRequest(BaseModel):
    """Simplified image request for mobile."""
    prompt: str
    size: str = "512x512"  # Smaller default for mobile


class MobileResponse(BaseModel):
    """Lightweight response for mobile."""
    id: str
    status: str
    result: Optional[str] = None
    thumbnail: Optional[str] = None  # Compressed preview
    cached: bool = False


class PaginatedResponse(BaseModel):
    """Paginated list response."""
    items: List[dict]
    total: int
    page: int
    page_size: int
    has_more: bool


@router.post("/text", response_model=MobileResponse)
async def mobile_generate_text(request: MobileTextRequest):
    """Generate text - mobile optimized."""
    from services import GroqService
    service = GroqService()

    result = await service.generate(
        prompt=request.prompt,
        model=request.model,
        max_tokens=request.max_tokens,
    )

    return MobileResponse(
        id="gen_mobile_text",
        status="completed",
        result=result.get("text", ""),
    )


@router.post("/image", response_model=MobileResponse)
async def mobile_generate_image(request: MobileImageRequest):
    """Generate image - mobile optimized with smaller sizes."""
    from services import StableDiffusionService
    service = StableDiffusionService()

    result = await service.generate(
        prompt=request.prompt,
        width=512,
        height=512,
    )

    return MobileResponse(
        id="gen_mobile_image",
        status="completed",
        result=result.get("image_url", ""),
    )


@router.get("/history")
async def mobile_get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=50),
    type: Optional[str] = None,
):
    """Get generation history - paginated for mobile."""
    from database import db

    offset = (page - 1) * page_size
    generations = await db.get_user_generations(
        user_id="mobile_user",  # Would come from auth
        limit=page_size
    )

    return PaginatedResponse(
        items=generations,
        total=len(generations),
        page=page,
        page_size=page_size,
        has_more=len(generations) == page_size,
    )


@router.get("/quick-actions")
async def mobile_quick_actions():
    """Get quick action suggestions for mobile."""
    return {
        "suggestions": [
            {"icon": "📝", "action": "text", "label": "Write something"},
            {"icon": "🎨", "action": "image", "label": "Create art"},
            {"icon": "🎬", "action": "video", "label": "Make video"},
            {"icon": "🧊", "action": "3d", "label": "3D model"},
        ],
        "recent": [],
    }


@router.get("/status")
async def mobile_status():
    """Quick status check for mobile."""
    return {
        "status": "ok",
        "services": {
            "text": True,
            "image": True,
            "video": False,
            "3d": False,
        },
    }
