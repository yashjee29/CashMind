"""
Tests for ICAI Announcement Icon Validation
Verifies catalog matching, unapproved icon filtering, and URL/emoji rejection.
"""

from app.modules.generate.announcements.icon_validator import sanitize_icon_identifier, validate_and_sanitize_icons
from app.modules.generate.announcements.schemas import AnnouncementResourceLink, AnnouncementSection


def test_sanitize_icon_identifier():
    approved = {"target", "book-open", "graduation-cap", "trophy"}

    # Exact match
    assert sanitize_icon_identifier("target", approved) == "target"

    # Case-insensitive match
    assert sanitize_icon_identifier("BOOK-OPEN", approved) == "book-open"

    # Unapproved / invented icon
    assert sanitize_icon_identifier("rocket_ship", approved) is None
    assert sanitize_icon_identifier("fire", approved) is None

    # Discord emoji markdown rejection
    assert sanitize_icon_identifier("<:target:1234567890>", approved) is None

    # URL rejection
    assert sanitize_icon_identifier("https://example.com/icon.png", approved) is None


def test_validate_and_sanitize_icons_across_sections_and_links():
    approved_list = ["target", "book-open", "trophy"]

    sections = [
        AnnouncementSection(heading="Section 1", icon="target"),
        AnnouncementSection(heading="Section 2", icon="invented_icon"),
        AnnouncementSection(heading="Section 3", icon=None),
    ]

    links = [
        AnnouncementResourceLink(label="Study", url="https://example.com", icon="book-open"),
        AnnouncementResourceLink(label="Contest", url="https://example.com/contest", icon="unapproved"),
    ]

    validate_and_sanitize_icons(sections, links, available_icons=approved_list)

    assert sections[0].icon == "target"
    assert sections[1].icon is None  # Reset to None because not in approved list
    assert sections[2].icon is None

    assert links[0].icon == "book-open"
    assert links[1].icon is None  # Reset to None because not in approved list


def test_empty_available_icons_resets_all():
    """When no approved catalog is provided, all icons must be None."""
    sections = [AnnouncementSection(heading="Focus", icon="target")]
    links = [AnnouncementResourceLink(label="Link", url="https://example.com", icon="target")]

    validate_and_sanitize_icons(sections, links, available_icons=[])

    assert sections[0].icon is None
    assert links[0].icon is None
