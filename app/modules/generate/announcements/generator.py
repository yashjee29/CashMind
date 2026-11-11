"""
ICAI Announcement Generator Engine
Orchestrates prompt generation, model invocation, link preservation, and icon sanitization.
"""

from typing import Tuple
from app.core.exceptions import OutputValidationError
from app.core.providers.groq_provider import GroqProvider, get_groq_provider
from app.core.responses import ResponseMetadata
from app.modules.generate.announcements.icon_validator import validate_and_sanitize_icons
from app.modules.generate.announcements.link_validator import validate_and_preserve_links
from app.modules.generate.announcements.prompts import (
    PROMPT_VERSION,
    build_announcement_craft_post_prompt,
    build_announcement_generate_prompt,
)
from app.modules.generate.announcements.schemas import (
    AnnouncementCraftPostData,
    AnnouncementCraftPostRequest,
    AnnouncementData,
    AnnouncementGenerateRequest,
    AnnouncementSection,
)


class AnnouncementGenerator:
    """Generates structured, motivational ICAI announcements from topics and instructions."""

    def __init__(self, provider: GroqProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> GroqProvider:
        return self._provider or get_groq_provider()

    async def generate(
        self,
        request: AnnouncementGenerateRequest,
    ) -> Tuple[AnnouncementData, ResponseMetadata]:
        """Executes announcement generation pipeline."""
        messages = build_announcement_generate_prompt(
            topic=request.topic,
            instructions=request.instructions,
            tone=request.tone,
            language=request.language,
            links=request.links,
            available_icons=request.available_icons,
        )

        result = await self.provider.generate_completion(
            task="announcement_generate",
            messages=messages,
        )

        parsed_json = result.get("parsed_json")
        if not isinstance(parsed_json, dict):
            raise OutputValidationError(
                "Model failed to return a valid JSON object for announcement generation.",
                details={"raw_content": result.get("content")},
            )

        # Parse sections
        raw_sections = parsed_json.get("sections") or []
        sections = []
        for sec in raw_sections:
            if isinstance(sec, dict) and sec.get("heading"):
                items = [str(it).strip() for it in sec.get("items", []) if str(it).strip()]
                sections.append(
                    AnnouncementSection(
                        heading=str(sec["heading"]).strip(),
                        icon=sec.get("icon"),
                        content=str(sec.get("content", "")).strip() or None,
                        items=items,
                    )
                )

        # Build raw data object
        title = str(parsed_json.get("title", "")).strip()
        if not title:
            # Fallback title if missing
            title = request.topic.strip() if request.topic else "ICAI Community Announcement"

        subtitle = parsed_json.get("subtitle")
        subtitle_clean = str(subtitle).strip() if subtitle else None

        intro = parsed_json.get("introduction")
        intro_clean = str(intro).strip() if intro else None

        closing = parsed_json.get("closing_message")
        closing_clean = str(closing).strip() if closing else None

        footer = parsed_json.get("footer")
        footer_clean = str(footer).strip() if footer else "ICAI Study Community"

        # Validate and preserve links strictly: model cannot invent links
        model_links_raw = parsed_json.get("links") or []
        model_links = []
        for ml in model_links_raw:
            if isinstance(ml, dict) and ml.get("url"):
                model_links.append(ml)

        validated_links = validate_and_preserve_links(
            model_links=model_links,
            user_links=request.links,
        )

        # Validate and sanitize icon identifiers against approved catalog
        validate_and_sanitize_icons(
            sections=sections,
            links=validated_links,
            available_icons=request.available_icons,
        )

        data = AnnouncementData(
            type="icai_announcement",
            title=title,
            subtitle=subtitle_clean,
            introduction=intro_clean,
            sections=sections,
            links=validated_links,
            closing_message=closing_clean,
            footer=footer_clean,
        )

        metadata = ResponseMetadata(
            model=result.get("model", "unknown"),
            provider="groq",
            prompt_version=PROMPT_VERSION,
        )

        return data, metadata

    async def craft_post(
        self,
        request: AnnouncementCraftPostRequest,
    ) -> Tuple[AnnouncementCraftPostData, ResponseMetadata]:
        """Crafts a complete, motivational Discord announcement post."""
        messages = build_announcement_craft_post_prompt(
            title=request.title,
            url=request.url,
            roles=request.roles,
            custom_emojis=request.custom_emojis,
            tone=request.tone,
        )

        result = await self.provider.generate_completion(
            task="announcement_craft_post",
            messages=messages,
        )

        parsed_json = result.get("parsed_json")
        if not isinstance(parsed_json, dict):
            raw_text = str(result.get("content", "")).strip()
            headline = f"📢 **{request.title}**"
            roles_str = " ".join(request.roles) if request.roles else "@everyone"
            content = f"{headline}\n\n{roles_str}\n\n{raw_text}\n\n🔗 **Official Link:**\n{request.url}"
            summary = request.title
        else:
            headline = str(parsed_json.get("headline", "")).strip() or f"📢 **{request.title}**"
            content = str(parsed_json.get("content", "")).strip()
            summary = str(parsed_json.get("summary", "")).strip() or request.title

            if not content:
                roles_str = " ".join(request.roles) if request.roles else "@everyone"
                content = f"{headline}\n\n{roles_str}\n\n{request.title}\n\n🔗 **Official Link:**\n{request.url}"

        # Ensure official URL is preserved at bottom if model omitted it
        if request.url and request.url not in content:
            content += f"\n\n🔗 **Check Your Results / Details:**\n{request.url}"

        data = AnnouncementCraftPostData(
            headline=headline,
            content=content,
            summary=summary,
        )

        metadata = ResponseMetadata(
            model=result.get("model", "unknown"),
            provider="groq",
            prompt_version=PROMPT_VERSION,
        )
        return data, metadata
