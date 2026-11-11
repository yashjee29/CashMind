"""
Moderation Reason Input and Output Validators
Enforces strict sanitization, bounds checking, and output invariants.
"""

import re
from app.core.exceptions import ValidationError
from app.modules.generate.moderation.schemas import ModerationRewriteRequest

# Regex pattern to detect URLs or links
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# Patterns for emojis or Discord mentions
EMOJI_PATTERN = re.compile(r"<a?:\w+:\d+>|[\U00010000-\U0010ffff]")


def validate_moderation_input(request: ModerationRewriteRequest) -> None:
    """Pre-flight sanity checks on moderation rewrite request."""
    if not request.reason or not request.reason.strip():
        raise ValidationError("Reason cannot be empty or whitespace.")

    if len(request.reason.strip()) < 3:
        raise ValidationError("Reason is too brief to meaningfully rewrite.")

    if len(request.reason) > 2000:
        raise ValidationError("Reason exceeds maximum allowed length of 2000 characters.")


def sanitize_moderation_output(rewritten_text: str, max_length: int = 500) -> str:
    """
    Enforces post-generation rules:
    - Strips URLs if any accidentally appeared
    - Strips extraneous emojis
    - Ensures length does not exceed max_length
    """
    cleaned = rewritten_text.strip()

    # Moderation reasons must NEVER contain external URLs or links
    if URL_PATTERN.search(cleaned):
        cleaned = URL_PATTERN.sub("", cleaned).strip()

    # Remove raw emojis if present
    cleaned = EMOJI_PATTERN.sub("", cleaned).strip()

    # Normalize double spaces and trim
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Enforce maximum length
    if len(cleaned) > max_length:
        # Trim gracefully at the last sentence or period before max_length
        truncated = cleaned[:max_length].strip()
        last_punct = max(truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?"))
        if last_punct > max_length // 2:
            cleaned = truncated[: last_punct + 1]
        else:
            cleaned = truncated

    return cleaned
