"""
ICAI Announcement Schemas
Strict Pydantic request and response models for announcement generation and rewriting.
"""

from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.responses import SuccessResponse


class AnnouncementOperation(str, Enum):
    """Supported announcement operations."""

    GENERATE = "generate"
    REWRITE = "rewrite"


class AnnouncementResourceLink(BaseModel):
    """User-provided resource link for ICAI announcements."""

    label: str = Field(
        ...,
        description="Display label for the link button or hyperlink",
        min_length=1,
        max_length=100,
    )
    url: str = Field(
        ...,
        description="Target resource URL (must be valid http/https)",
        max_length=1000,
    )
    icon: Optional[str] = Field(
        default=None,
        description="Optional icon identifier from approved catalog",
        max_length=50,
    )

    @field_validator("label", mode="before")
    @classmethod
    def strip_label(cls, v: object) -> str:
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else "Resource"
        return "Resource"

    @field_validator("url", mode="before")
    @classmethod
    def strip_url(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("URL must be a string.")
        stripped = v.strip()
        if not (stripped.startswith("http://") or stripped.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return stripped


class AnnouncementSection(BaseModel):
    """Structured section within an ICAI announcement."""

    heading: str = Field(
        ...,
        description="Section heading/title",
        min_length=1,
        max_length=150,
    )
    icon: Optional[str] = Field(
        default=None,
        description="Approved icon identifier or null",
        max_length=50,
    )
    content: Optional[str] = Field(
        default=None,
        description="Main explanatory or descriptive paragraph",
        max_length=2000,
    )
    items: List[str] = Field(
        default_factory=list,
        description="Bullet action points, key study tips, or checklist items",
    )


class AnnouncementGenerateRequest(BaseModel):
    """Input payload for generating a fresh ICAI announcement."""

    operation: Literal["generate"] = "generate"
    topic: Optional[str] = Field(
        default=None,
        description="Announcement topic or theme (e.g. 'Daily study targets', 'Revision tips')",
        max_length=500,
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Specific instructions or guidelines for content creation",
        max_length=2000,
    )
    existing_content: Optional[str] = Field(
        default=None,
        description="Unused in generate operation",
    )
    tone: str = Field(
        default="motivational",
        description="Desired tone: motivational, friendly, formal, energetic",
        max_length=50,
    )
    language: str = Field(
        default="en",
        description="Output language code",
        max_length=20,
    )
    links: List[AnnouncementResourceLink] = Field(
        default_factory=list,
        description="Resource links to attach to the announcement",
    )
    available_icons: List[str] = Field(
        default_factory=list,
        description="List of approved icon identifiers supplied by Cash Mod",
    )

    @model_validator(mode="after")
    def check_topic_or_instructions(self) -> "AnnouncementGenerateRequest":
        topic_clean = self.topic.strip() if self.topic else ""
        inst_clean = self.instructions.strip() if self.instructions else ""
        if not topic_clean and not inst_clean:
            raise ValueError("Either 'topic' or 'instructions' must be provided for announcement generation.")
        return self


class AnnouncementRewriteRequest(BaseModel):
    """Input payload for rewriting an existing ICAI announcement draft."""

    operation: Literal["rewrite"] = "rewrite"
    existing_content: str = Field(
        ...,
        description="Existing announcement draft to be improved and formatted",
        min_length=5,
        max_length=5000,
    )
    topic: Optional[str] = Field(
        default=None,
        description="Optional context topic",
        max_length=500,
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Optional rewriting instructions (e.g. 'Make it more energetic')",
        max_length=2000,
    )
    tone: str = Field(
        default="motivational",
        description="Desired tone: motivational, friendly, formal, energetic",
        max_length=50,
    )
    language: str = Field(
        default="en",
        description="Output language code",
        max_length=20,
    )
    links: List[AnnouncementResourceLink] = Field(
        default_factory=list,
        description="Resource links to attach or preserve",
    )
    available_icons: List[str] = Field(
        default_factory=list,
        description="List of approved icon identifiers supplied by Cash Mod",
    )

    @field_validator("existing_content", mode="before")
    @classmethod
    def validate_content(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("existing_content must be a string.")
        stripped = v.strip()
        if len(stripped) < 5:
            raise ValueError("existing_content must contain at least 5 characters.")
        return stripped


class AnnouncementData(BaseModel):
    """Structured ICAI announcement response consumed by TypeScript Cash Mod."""

    type: Literal["icai_announcement"] = "icai_announcement"
    title: str = Field(
        ...,
        description="Main headline title of the announcement",
        min_length=1,
        max_length=200,
    )
    subtitle: Optional[str] = Field(
        default=None,
        description="Optional subtitle or category label",
        max_length=200,
    )
    introduction: Optional[str] = Field(
        default=None,
        description="Introductory context or opening hook",
        max_length=1000,
    )
    sections: List[AnnouncementSection] = Field(
        default_factory=list,
        description="Structured sections containing headings, content, and checklist items",
    )
    links: List[AnnouncementResourceLink] = Field(
        default_factory=list,
        description="Preserved and verified resource links",
    )
    closing_message: Optional[str] = Field(
        default=None,
        description="Closing motivational sign-off",
        max_length=500,
    )
    footer: Optional[str] = Field(
        default="ICAI Study Community",
        description="Footer text indicating community origin",
        max_length=200,
    )


class AnnouncementResponse(SuccessResponse[AnnouncementData]):
    """Final API response envelope for ICAI announcements."""
    pass


class AnnouncementCraftPostRequest(BaseModel):
    """Input payload for crafting a complete motivational Discord announcement post."""

    title: str = Field(
        ...,
        description="Official announcement title or headline from ICAI",
        min_length=3,
        max_length=1000,
    )
    url: str = Field(
        ...,
        description="Target official link or PDF URL",
        min_length=3,
        max_length=1000,
    )
    roles: List[str] = Field(
        default_factory=list,
        description="Target role tags e.g. ['@Foundation', '@Inter', '@Final'] or Discord role mentions",
    )
    custom_emojis: Optional[dict[str, str]] = Field(
        default=None,
        description="Mapping of custom Discord emoji tags to use",
    )
    tone: str = Field(
        default="motivational",
        description="Desired tone: motivational, empathetic, inspiring, celebratory",
        max_length=50,
    )


class AnnouncementCraftPostData(BaseModel):
    """Crafted motivational Discord announcement post."""

    headline: str = Field(
        ...,
        description="Catchy headline with emojis",
    )
    content: str = Field(
        ...,
        description="Full ready-to-post Discord message in Markdown with role mentions, custom emojis, paragraphs, and link.",
    )
    summary: str = Field(
        ...,
        description="Brief 1-sentence summary of the announcement",
    )


class AnnouncementCraftPostResponse(SuccessResponse[AnnouncementCraftPostData]):
    """Final API response envelope for crafted announcement post."""
    pass
