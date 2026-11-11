"""
ICAI Announcement Service Facade
High-level service interface for announcement generation and rewriting.
"""

from typing import Optional
from app.modules.generate.announcements.generator import AnnouncementGenerator
from app.modules.generate.announcements.rewriter import AnnouncementRewriter
from app.modules.generate.announcements.schemas import (
    AnnouncementCraftPostRequest,
    AnnouncementCraftPostResponse,
    AnnouncementGenerateRequest,
    AnnouncementResponse,
    AnnouncementRewriteRequest,
)


class AnnouncementService:
    """Service facade coordinating ICAI announcement generation and rewriting."""

    def __init__(
        self,
        generator: Optional[AnnouncementGenerator] = None,
        rewriter: Optional[AnnouncementRewriter] = None,
    ) -> None:
        self.generator = generator or AnnouncementGenerator()
        self.rewriter = rewriter or AnnouncementRewriter()

    async def generate_announcement(
        self,
        request: AnnouncementGenerateRequest,
    ) -> AnnouncementResponse:
        """Generates a structured announcement from topics or instructions."""
        data, metadata = await self.generator.generate(request)
        return AnnouncementResponse(
            success=True,
            data=data,
            metadata=metadata,
        )

    async def rewrite_announcement(
        self,
        request: AnnouncementRewriteRequest,
    ) -> AnnouncementResponse:
        """Rewrites and structures an existing announcement draft."""
        data, metadata = await self.rewriter.rewrite(request)
        return AnnouncementResponse(
            success=True,
            data=data,
            metadata=metadata,
        )

    async def craft_post(
        self,
        request: AnnouncementCraftPostRequest,
    ) -> AnnouncementCraftPostResponse:
        """Crafts a complete, motivational Discord announcement post."""
        data, metadata = await self.generator.craft_post(request)
        return AnnouncementCraftPostResponse(
            success=True,
            data=data,
            metadata=metadata,
        )


_announcement_service_instance: Optional[AnnouncementService] = None


def get_announcement_service() -> AnnouncementService:
    """Retrieves or initializes singleton AnnouncementService."""
    global _announcement_service_instance
    if _announcement_service_instance is None:
        _announcement_service_instance = AnnouncementService()
    return _announcement_service_instance
