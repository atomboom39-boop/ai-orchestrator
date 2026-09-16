"""
🎭 AI Orchestrator - Multi-service AI router
Routes requests to the best AI service for the job.

User → Claude → Orchestrator → Multiple AI Services
                                    ├─ Groq (text - fastest)
                                    ├─ Stable Diffusion (image)
                                    ├─ Runway ML (video)
                                    └─ Luma AI (3D)
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List

from models import (
    TextRequest, TextResponse,
    ImageRequest, ImageResponse,
    VideoRequest, VideoResponse,
    ThreeDRequest, ThreeDResponse,
    ServiceInfo, ServiceStatus, ErrorResponse,
)
from services import (
    GroqService,
    StableDiffusionService,
    RunwayService,
    LumaService,
)

# Load environment variables
load_dotenv()

# Service instances
services = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    services["groq"] = GroqService()
    services["sd"] = StableDiffusionService()
    services["runway"] = RunwayService()
    services["luma"] = LumaService()

    print("🎭 AI Orchestrator started!")
    print("━" * 50)
    for name, service in services.items():
        status = await service.health_check()
        status_emoji = "✅" if status else "⚠️  (not configured)"
        print(f"  {name}: {status_emoji}")
    print("━" * 50)

    yield

    # Cleanup
    for service in services.values():
        await service.close()
    print("🎭 AI Orchestrator shut down.")


# Create FastAPI app
app = FastAPI(
    title="AI Orchestrator",
    description="Multi-AI service orchestrator with unified interface",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include sub-app routers (routers already have their full prefixes)
try:
    from payments.api import router as billing_router
    app.include_router(billing_router)
    print("✅ Billing API mounted")
except ImportError as e:
    print(f"⚠️ Billing API not mounted: {e}")

try:
    from api.mobile import router as mobile_router
    app.include_router(mobile_router)
    print("✅ Mobile API mounted")
except ImportError as e:
    print(f"⚠️ Mobile API not mounted: {e}")

# Mount static files for simple UI
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print("✅ Static UI mounted")
except Exception as e:
    print(f"⚠️ Static UI not mounted: {e}")


# --- Health & Info ---

@app.get("/")
async def root():
    """Redirect to simple UI."""
    return FileResponse("static/index.html")


@app.get("/services", response_model=List[ServiceInfo])
async def list_services():
    """List all services and their status."""
    service_list = []

    info_map = {
        "groq": ServiceInfo(
            name="Groq",
            description="Ultra-fast text generation",
            capabilities=["text", "chat", "code"],
        ),
        "sd": ServiceInfo(
            name="Stable Diffusion",
            description="Image generation",
            capabilities=["image", "art"],
        ),
        "runway": ServiceInfo(
            name="Runway ML",
            description="Video generation",
            capabilities=["video", "animation"],
        ),
        "luma": ServiceInfo(
            name="Luma AI",
            description="3D model generation",
            capabilities=["3d", "modeling"],
        ),
    }

    for name, service in services.items():
        info = info_map[name]
        status = await service.health_check()
        info.status = ServiceStatus.AVAILABLE if status else ServiceStatus.UNAVAILABLE
        service_list.append(info)

    return service_list


# --- Text Generation (Groq) ---

@app.post("/generate/text", response_model=TextResponse)
async def generate_text(request: TextRequest):
    """Generate text using Groq (ultra-fast inference)."""
    result = await services["groq"].generate(
        prompt=request.prompt,
        model=request.model,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )

    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])

    return TextResponse(**result)


# --- Image Generation (Stable Diffusion) ---

@app.post("/generate/image", response_model=ImageResponse)
async def generate_image(request: ImageRequest):
    """Generate image using Stable Diffusion."""
    size_parts = request.size.value.split("x")
    result = await services["sd"].generate(
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        width=int(size_parts[0]),
        height=int(size_parts[1]),
        num_images=request.num_images,
    )

    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])

    # Handle different response formats
    if "images" in result:
        first = result["images"][0]
        if first.startswith("data:"):
            # Already a data URI (e.g. local_sd / Pollinations)
            return ImageResponse(
                image_url=first,
                service=result.get("service", "local_sd"),
            )
        return ImageResponse(
            image_url=f"data:image/png;base64,{first}",
            service=result.get("service", "local_sd"),
        )
    else:
        return ImageResponse(**result)


# --- Video Generation (Runway) ---

@app.post("/generate/video", response_model=VideoResponse)
async def generate_video(request: VideoRequest):
    """Generate video using Runway ML."""
    result = await services["runway"].generate(
        prompt=request.prompt,
        image_url=request.image_url,
        duration=request.duration.value,
    )

    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])

    return VideoResponse(
        video_url=result.get("video_url", ""),
        duration=request.duration.value,
        service="runway",
    )


# --- 3D Generation (Luma AI) ---

@app.post("/generate/3d", response_model=ThreeDResponse)
async def generate_3d(request: ThreeDRequest):
    """Generate 3D model using Luma AI."""
    result = await services["luma"].generate(
        prompt=request.prompt,
        image_url=request.image_url,
    )

    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])

    return ThreeDResponse(
        model_url=result.get("model_url", ""),
        thumbnail_url=result.get("thumbnail_url"),
        service="luma",
    )


# --- Status Check ---

@app.get("/status/{service_name}/{task_id}")
async def check_status(service_name: str, task_id: str):
    """Check async task status (video/3D generation)."""
    if service_name == "runway":
        result = await services["runway"].check_status(task_id)
    elif service_name == "luma":
        result = await services["luma"].check_status(task_id)
    else:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")

    return result


# --- Main ---

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    print(f"🚀 Starting AI Orchestrator on http://{host}:{port}")
    print(f"📖 Docs available at http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port)
