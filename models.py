"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# --- Enums ---

class ServiceStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"


class ImageSize(str, Enum):
    SMALL = "512x512"
    MEDIUM = "1024x1024"
    LARGE = "1536x1536"


class VideoDuration(str, Enum):
    SHORT = "5s"
    MEDIUM = "10s"
    LONG = "16s"


# --- Request Models ---

class TextRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt to generate response for")
    model: str = Field(default="openai/gpt-oss-120b", description="Groq model name")
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class ImageRequest(BaseModel):
    prompt: str = Field(..., description="Image generation prompt")
    negative_prompt: Optional[str] = Field(default=None, description="What to avoid")
    size: ImageSize = Field(default=ImageSize.MEDIUM)
    num_images: int = Field(default=1, ge=1, le=4)


class VideoRequest(BaseModel):
    prompt: str = Field(..., description="Video generation prompt")
    image_url: Optional[str] = Field(default=None, description="Reference image URL")
    duration: VideoDuration = Field(default=VideoDuration.SHORT)


class ThreeDRequest(BaseModel):
    prompt: str = Field(..., description="3D generation prompt")
    image_url: Optional[str] = Field(default=None, description="Reference image URL")


# --- Response Models ---

class TextResponse(BaseModel):
    text: str
    model: str
    tokens_used: int
    service: str = "groq"


class ImageResponse(BaseModel):
    image_url: str
    revised_prompt: Optional[str] = None
    service: str


class VideoResponse(BaseModel):
    video_url: str
    duration: str
    service: str = "runway"


class ThreeDResponse(BaseModel):
    model_url: str
    thumbnail_url: Optional[str] = None
    service: str = "luma"

    model_config = {"protected_namespaces": ()}


class ServiceInfo(BaseModel):
    name: str
    status: ServiceStatus = ServiceStatus.UNAVAILABLE
    description: str
    capabilities: List[str]


class ErrorResponse(BaseModel):
    error: str
    service: str
    detail: Optional[str] = None
