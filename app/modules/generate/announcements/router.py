"""
ICAI Announcement FastAPI Router
Exposes HTTP endpoints for generating and rewriting ICAI announcements.
"""

from fastapi import APIRouter, Depends, status
from app.core.security import verify_internal_auth
from app.modules.generate.announcements.schemas import (
    AnnouncementCraftPostRequest,
    AnnouncementCraftPostResponse,
    AnnouncementGenerateRequest,
    AnnouncementResponse,
    AnnouncementRewriteRequest,
)
from app.modules.generate.announcements.service import (
    AnnouncementService,
    get_announcement_service,
)

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.post(
    "/generate",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a structured ICAI announcement",
    description="Creates a motivational, student-friendly announcement from topic or instructions.",
    dependencies=[Depends(verify_internal_auth)],
)
async def generate_announcement(
    payload: AnnouncementGenerateRequest,
    service: AnnouncementService = Depends(get_announcement_service),
) -> AnnouncementResponse:
    """Generates structured announcement data with validated icons and links."""
    return await service.generate_announcement(payload)


@router.post(
    "/rewrite",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_200_OK,
    summary="Rewrite and polish an ICAI announcement draft",
    description="Improves readability, motivational tone, and structure while strictly preserving factual data.",
    dependencies=[Depends(verify_internal_auth)],
)
async def rewrite_announcement(
    payload: AnnouncementRewriteRequest,
    service: AnnouncementService = Depends(get_announcement_service),
) -> AnnouncementResponse:
    """Rewrites and enhances an announcement draft into structured format."""
    return await service.rewrite_announcement(payload)


@router.post(
    "/craft-post",
    response_model=AnnouncementCraftPostResponse,
    status_code=status.HTTP_200_OK,
    summary="Craft motivational Discord announcement post",
    description="Takes title, URL, roles, and custom emojis to generate a complete dynamic Discord announcement.",
    dependencies=[Depends(verify_internal_auth)],
)
async def craft_announcement_post(
    payload: AnnouncementCraftPostRequest,
    service: AnnouncementService = Depends(get_announcement_service),
) -> AnnouncementCraftPostResponse:
    """Crafts complete motivational Discord announcement post."""
    return await service.craft_post(payload)
