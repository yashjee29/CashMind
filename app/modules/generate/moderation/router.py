"""
Moderation Reason FastAPI Router
Exposes HTTP endpoints for rewriting moderation reasons.
"""

from fastapi import APIRouter, Depends, status
from app.core.security import verify_internal_auth
from app.modules.generate.moderation.schemas import (
    ModerationRewriteRequest,
    ModerationRewriteResponse,
)
from app.modules.generate.moderation.service import (
    ModerationService,
    get_moderation_service,
)

router = APIRouter(prefix="/moderation", tags=["Moderation"])


@router.post(
    "/rewrite",
    response_model=ModerationRewriteResponse,
    status_code=status.HTTP_200_OK,
    summary="Rewrite a moderation reason",
    description="Rewrites an incident or reported moderation reason into a formal, authoritative, action-appropriate reason.",
    dependencies=[Depends(verify_internal_auth)],
)
async def rewrite_moderation_reason(
    payload: ModerationRewriteRequest,
    service: ModerationService = Depends(get_moderation_service),
) -> ModerationRewriteResponse:
    """Processes rewriting for warning, timeout, kick, or ban actions."""
    return await service.rewrite_reason(payload)
