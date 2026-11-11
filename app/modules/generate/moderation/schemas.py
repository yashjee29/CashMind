"""
Moderation Reason Rewriter Schemas
Strict Pydantic request and response models for moderation reason rewriting.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.core.responses import ResponseMetadata, SuccessResponse


class ModerationAction(str, Enum):
    """Supported moderation sanction actions."""

    WARNING = "warning"
    TIMEOUT = "timeout"
    KICK = "kick"
    BAN = "ban"


class ModerationRewriteRequest(BaseModel):
    """Input payload for rewriting a moderation reason."""

    action: ModerationAction = Field(
        ...,
        description="Moderation action: warning, timeout, kick, or ban",
    )
    reason: str = Field(
        ...,
        description="Original reported reason submitted by moderator or reporter",
        min_length=3,
        max_length=2000,
    )
    language: str = Field(
        default="en",
        description="Desired output language (defaults to English)",
        max_length=20,
    )
    additional_context: Optional[str] = Field(
        default=None,
        description="Additional verified incident context or notes",
        max_length=2000,
    )
    max_length: Optional[int] = Field(
        default=500,
        description="Maximum length constraint for the rewritten reason",
        ge=50,
        le=1000,
    )

    @field_validator("reason", mode="before")
    @classmethod
    def strip_and_validate_reason(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("Reason must be a valid string.")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Reason cannot be empty or pure whitespace.")
        return stripped

    @field_validator("additional_context", mode="before")
    @classmethod
    def strip_context(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else None
        return str(v)


class ModerationRewriteData(BaseModel):
    """Validated structured output payload for moderation rewriting."""

    action: str = Field(description="The moderation action applied")
    original_reason: str = Field(description="The original user-submitted reason preserved for audit")
    rewritten_reason: str = Field(description="The formal, authoritative, rewritten moderation reason")
    language: str = Field(description="Output language code")


class ModerationRewriteResponse(SuccessResponse[ModerationRewriteData]):
    """Final API response envelope for moderation rewriting."""
    pass
