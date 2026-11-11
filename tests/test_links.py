"""
Tests for ICAI Announcement Resource Link Validation
Verifies exact URL preservation, prevention of LLM-invented URLs, and syntax checks.
"""

import pytest
from app.core.exceptions import ValidationError
from app.modules.generate.announcements.link_validator import (
    validate_and_preserve_links,
    validate_url_syntax,
)
from app.modules.generate.announcements.schemas import AnnouncementResourceLink


def test_validate_url_syntax():
    # Valid HTTPS and HTTP
    validate_url_syntax("https://icai.org/bos")
    validate_url_syntax("http://example.com/test?param=1#anchor")

    # Invalid schemes
    with pytest.raises(ValidationError) as exc:
        validate_url_syntax("ftp://files.example.com")
    assert "not allowed" in str(exc.value)

    with pytest.raises(ValidationError):
        validate_url_syntax("javascript:alert(1)")

    # Missing domain
    with pytest.raises(ValidationError):
        validate_url_syntax("https://")


def test_preserves_supplied_urls_exactly():
    user_links = [
        AnnouncementResourceLink(label="Study Material", url="https://icai.org/material?ref=123&session=CA"),
        AnnouncementResourceLink(label="Practice Papers", url="https://icai.org/rtp"),
    ]

    # Model returns slightly different labels, but links must match user links exactly
    model_links = [
        AnnouncementResourceLink(label="Download ICAI Material", url="https://icai.org/material?ref=123&session=CA"),
        AnnouncementResourceLink(label="Practice Papers", url="https://icai.org/rtp"),
    ]

    preserved = validate_and_preserve_links(model_links, user_links)

    assert len(preserved) == 2
    assert preserved[0].url == "https://icai.org/material?ref=123&session=CA"
    assert preserved[1].url == "https://icai.org/rtp"


def test_forbids_llm_invented_urls():
    """If the user provided no links, the output must be empty, even if the LLM hallucinated links."""
    user_links = []
    model_links = [
        AnnouncementResourceLink(label="Fake Link", url="https://fake-hallucinated-url.com")
    ]

    preserved = validate_and_preserve_links(model_links, user_links)
    assert preserved == []


def test_ignores_llm_hallucinated_extra_urls():
    """If user provided 1 link and LLM invented a 2nd link, the 2nd link must be dropped."""
    user_links = [AnnouncementResourceLink(label="Official", url="https://icai.org")]
    model_links = [
        AnnouncementResourceLink(label="Official", url="https://icai.org"),
        AnnouncementResourceLink(label="Hallucinated", url="https://unauthorized-extra.com"),
    ]

    preserved = validate_and_preserve_links(model_links, user_links)
    assert len(preserved) == 1
    assert preserved[0].url == "https://icai.org"
