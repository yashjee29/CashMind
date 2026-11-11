"""
ICAI Announcement Resource Link Validator
Enforces exact preservation of user-supplied URLs, forbids LLM link invention,
and validates syntax and allowed schemes.
"""

from typing import Any, List, Optional
from urllib.parse import urlparse
from app.core.exceptions import ValidationError
from app.modules.generate.announcements.schemas import AnnouncementResourceLink

ALLOWED_SCHEMES = {"http", "https"}


def validate_url_syntax(url_str: str) -> None:
    """Verifies that a URL string has valid syntax and an allowed scheme."""
    try:
        parsed = urlparse(url_str.strip())
        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            raise ValidationError(
                f"URL scheme '{parsed.scheme}' is not allowed. Only HTTP and HTTPS are supported."
            )
        if not parsed.netloc:
            raise ValidationError(f"URL '{url_str}' is missing a valid domain host.")
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Invalid URL structure: {str(e)}")


def validate_and_preserve_links(
    model_links: Optional[List[Any]],
    user_links: Optional[List[AnnouncementResourceLink]],
) -> List[AnnouncementResourceLink]:
    """
    Enforces the strict link preservation contract:
    1. If user provided NO links, output MUST be empty list [].
       Any URLs hallucinated or invented by the model are strictly discarded.
    2. If user provided links, EVERY user link is preserved with its EXACT URL.
    3. The model's proposed label may be adopted if it is descriptive and non-empty.
    4. Model icon may be adopted if valid.
    5. URL syntax is strictly verified for http/https.
    """
    if not user_links:
        return []

    # Validate syntax of all user-supplied links
    for link in user_links:
        validate_url_syntax(link.url)

    # Index model-suggested links by exact URL to check if the model enriched labels/icons
    model_by_url = {}
    if model_links:
        for m_link in model_links:
            if not m_link:
                continue
            m_url = getattr(m_link, "url", None) or (m_link.get("url") if isinstance(m_link, dict) else None)
            m_label = getattr(m_link, "label", None) or (m_link.get("label") if isinstance(m_link, dict) else None)
            m_icon = getattr(m_link, "icon", None) or (m_link.get("icon") if isinstance(m_link, dict) else None)

            if m_url and isinstance(m_url, str):
                model_by_url[m_url.strip()] = {"label": m_label, "icon": m_icon}

    preserved_links: List[AnnouncementResourceLink] = []

    for u_link in user_links:
        exact_url = u_link.url.strip()
        matched_model = model_by_url.get(exact_url)

        # Determine label: prioritize user's label unless user had a generic placeholder
        label = u_link.label.strip() if u_link.label else ""
        if matched_model and matched_model.get("label"):
            model_lbl = str(matched_model["label"]).strip()
            if not label or label.lower() in ("link", "resource", "url"):
                label = model_lbl

        if not label:
            label = "Resource Link"

        # Determine icon: user icon if present, else model icon
        icon = u_link.icon
        if not icon and matched_model and matched_model.get("icon"):
            icon = str(matched_model["icon"]).strip()

        preserved_links.append(
            AnnouncementResourceLink(
                label=label,
                url=exact_url,  # Preserved byte-for-byte
                icon=icon,
            )
        )

    return preserved_links
