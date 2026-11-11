"""
CashMind Generate Module Aggregator Router
Aggregates Moderation, Announcements, and Module Health endpoints.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from app.core.providers.groq_provider import get_groq_provider
from app.modules.generate.announcements.router import router as announcements_router
from app.modules.generate.moderation.router import router as moderation_router

router = APIRouter(prefix="/generate")

# Include sub-feature routers
router.include_router(moderation_router)
router.include_router(announcements_router)


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    service: str
    version: str
    provider: str
    pool: dict
    models: dict


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Module Health and Readiness Check",
    description="Returns module availability, Groq key pool status, and configured models without exposing credentials.",
)
async def generate_health() -> HealthResponse:
    """Readiness endpoint verifying provider key pool and routing status."""
    provider = get_groq_provider()
    pool_status = provider.key_pool.get_status()
    models = provider.model_router.get_registered_models()

    is_healthy = bool(pool_status.get("pool_ready", False))

    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        service="cashmind-generate",
        version="1.0.0",
        provider="groq",
        pool=pool_status,
        models=models,
    )
