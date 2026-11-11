"""
Tests for Pydantic Request and Response Schemas
Verifies type constraints, default values, and boundary validations.
"""

import pytest
from pydantic import ValidationError
from app.modules.generate.announcements.schemas import (
    AnnouncementGenerateRequest,
    AnnouncementResourceLink,
    AnnouncementRewriteRequest,
    AnnouncementSection,
)
from app.modules.generate.moderation.schemas import ModerationAction, ModerationRewriteRequest


def test_moderation_request_schema():
    req = ModerationRewriteRequest(
        action=ModerationAction.WARNING,
        reason="User was violating chat rules.",
    )
    assert req.action == ModerationAction.WARNING
    assert req.language == "en"
    assert req.max_length == 500
    assert req.additional_context is None

    # Clamping bounds: max_length < 50 or > 1000 should raise ValidationError
    with pytest.raises(ValidationError):
        ModerationRewriteRequest(
            action=ModerationAction.TIMEOUT,
            reason="Rule violation",
            max_length=20,  # below minimum 50
        )


def test_announcement_generate_schema():
    req = AnnouncementGenerateRequest(
        topic="Study Tips",
        instructions="Focus on revision",
    )
    assert req.operation == "generate"
    assert req.tone == "motivational"
    assert req.links == []
    assert req.available_icons == []


def test_announcement_resource_link_schema():
    link = AnnouncementResourceLink(
        label="  Download RTP  ",
        url="  https://icai.org/rtp  ",
    )
    assert link.label == "Download RTP"
    assert link.url == "https://icai.org/rtp"

    # Invalid URL scheme
    with pytest.raises(ValidationError):
        AnnouncementResourceLink(label="Bad", url="ftp://files.org")
