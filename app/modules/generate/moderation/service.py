"""
Moderation Reason Service Facade
High-level service interface for moderation reason operations.
"""

from typing import Optional
from app.modules.generate.moderation.rewriter import ModerationRewriter
from app.modules.generate.moderation.schemas import (
    ModerationRewriteRequest,
    ModerationRewriteResponse,
)


class ModerationService:
    """Service facade coordinating moderation reason rewriting."""

    def __init__(self, rewriter: Optional[ModerationRewriter] = None) -> None:
        self.rewriter = rewriter or ModerationRewriter()

    async def rewrite_reason(self, request: ModerationRewriteRequest) -> ModerationRewriteResponse:
        """Processes and rewrites a moderation reason."""
        data, metadata = await self.rewriter.rewrite(request)
        return ModerationRewriteResponse(
            success=True,
            data=data,
            metadata=metadata,
        )


_moderation_service_instance: Optional[ModerationService] = None


def get_moderation_service() -> ModerationService:
    """Retrieves or initializes singleton ModerationService."""
    global _moderation_service_instance
    if _moderation_service_instance is None:
        _moderation_service_instance = ModerationService()
    return _moderation_service_instance
