"""
CashMind Internal Service Security
Verifies internal service requests between CashMod and CashMind.
"""

import secrets
from typing import Optional
from fastapi import Header, Request
from app.core.config import settings
from app.core.exceptions import AuthenticationError


async def verify_internal_auth(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> None:
    """
    Enforces authentication for internal service calls.
    Accepts API key via X-API-Key header or Bearer token.
    If CASHMIND_API_KEY is unset or empty, auth is bypassed (for dev).
    """
    expected_key = settings.CASHMIND_API_KEY
    if not expected_key:
        return

    provided_token: Optional[str] = None

    if x_api_key:
        provided_token = x_api_key.strip()
    elif authorization and authorization.startswith("Bearer "):
        provided_token = authorization[7:].strip()

    if not provided_token or not secrets.compare_digest(provided_token, expected_key):
        raise AuthenticationError("Invalid or missing internal service API key.")
