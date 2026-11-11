"""
ICAI Announcement Icon Validator
Enforces strict icon selection constraints against the approved Cash Mod icon catalog.
"""

from typing import List, Optional, Set
from app.modules.generate.announcements.schemas import AnnouncementResourceLink, AnnouncementSection


def sanitize_icon_identifier(icon_val: Optional[str], approved_set: Set[str]) -> Optional[str]:
    """
    Validates a single icon identifier:
    - Must be an exact match (case-insensitive) against the approved icon catalog
    - Rejects Discord emoji markdown (<:name:id>), raw URLs, or invented names
    - Returns exact approved identifier or None
    """
    if not icon_val or not isinstance(icon_val, str):
        return None

    cleaned = icon_val.strip().lower()

    # Reject if it looks like a URL, emoji snowflake, or markup
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return None
    if cleaned.startswith("<:") or cleaned.startswith("<a:"):
        return None

    # Check against approved catalog
    for approved in approved_set:
        if approved.strip().lower() == cleaned:
            return approved.strip()

    return None


def validate_and_sanitize_icons(
    sections: List[AnnouncementSection],
    links: List[AnnouncementResourceLink],
    available_icons: Optional[List[str]],
) -> None:
    """
    In-place validation and sanitization of icons across sections and links.
    Guarantees that no unauthorized icon identifiers are returned to Cash Mod.
    """
    if not available_icons:
        # If no icon catalog was supplied, reset all icons to None
        for sec in sections:
            sec.icon = None
        for link in links:
            link.icon = None
        return

    approved_set = {icon.strip() for icon in available_icons if icon and icon.strip()}

    for sec in sections:
        sec.icon = sanitize_icon_identifier(sec.icon, approved_set)

    for link in links:
        link.icon = sanitize_icon_identifier(link.icon, approved_set)
