"""
Tests for Moderation Reason Rewriter
Verifies warning, timeout, kick, ban, validation, sanitization, and strict writing policy.
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.core.exceptions import ValidationError
from app.core.providers.groq_provider import get_groq_provider
from app.modules.generate.moderation.schemas import ModerationAction, ModerationRewriteRequest
from app.modules.generate.moderation.validators import sanitize_moderation_output, validate_moderation_input


def test_validate_moderation_input_rejects_empty():
    from pydantic import ValidationError as PydanticValidationError

    # Pydantic schema validation rejects whitespace or <3 chars
    with pytest.raises(PydanticValidationError):
        ModerationRewriteRequest(action=ModerationAction.WARNING, reason="   ")

    with pytest.raises(PydanticValidationError):
        ModerationRewriteRequest(action=ModerationAction.WARNING, reason="ab")

    # Domain validator function checks
    valid_req = ModerationRewriteRequest(action=ModerationAction.WARNING, reason="Valid reported reason here")
    valid_req.reason = ""
    with pytest.raises(ValidationError):
        validate_moderation_input(valid_req)


def test_sanitize_moderation_output_strips_urls_and_emojis():
    raw = "User spammed general chat with links: https://malicious.com and <:cross:12345>."
    clean = sanitize_moderation_output(raw, max_length=500)
    assert "https://" not in clean
    assert "<:cross:" not in clean
    assert "User spammed general chat with links:" in clean


def test_sanitize_moderation_output_respects_max_length():
    long_text = "This is a very long sentence. " * 30
    clean = sanitize_moderation_output(long_text, max_length=100)
    assert len(clean) <= 100


@pytest.mark.parametrize(
    "action,mock_reason",
    [
        (
            "warning",
            "The reported user engaged in disruptive communication in general chat. Such behavior violates server rules and must cease immediately.",
        ),
        (
            "timeout",
            "The reported user repeatedly ignored moderator directives regarding disruptive messaging. A temporary communication restriction has been issued.",
        ),
        (
            "kick",
            "The reported user engaged in sustained violation of server guidelines. As a result, the user has been removed from the server.",
        ),
        (
            "ban",
            "The reported user engaged in severe misconduct violating core community safety standards. Server access has been revoked.",
        ),
    ],
)
def test_moderation_actions_rewrite_endpoint(client: TestClient, action: str, mock_reason: str):
    """Tests all 4 moderation actions via the HTTP endpoint with mocked Groq response."""
    mock_llm_result = {
        "content": '{"rewritten_reason": "' + mock_reason + '"}',
        "parsed_json": {"rewritten_reason": mock_reason},
        "model": "llama-3.3-70b-versatile",
        "provider": "groq",
    }

    with patch.object(
        get_groq_provider(), "generate_completion", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = mock_llm_result

        payload = {
            "action": action,
            "reason": "User was shouting and abusive in chat.",
            "language": "en",
            "additional_context": "Previous incident logged in mod log",
            "max_length": 500,
        }

        resp = client.post("/api/v1/generate/moderation/rewrite", json=payload)
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is True
        assert body["data"]["action"] == action
        assert body["data"]["original_reason"] == payload["reason"]
        assert body["data"]["rewritten_reason"] == mock_reason
        assert body["data"]["language"] == "en"
        assert body["metadata"]["provider"] == "groq"
        assert body["metadata"]["model"] == "llama-3.3-70b-versatile"

        # Verify no link or custom icon fields are present in moderation data
        data_keys = set(body["data"].keys())
        assert "links" not in data_keys
        assert "icons" not in data_keys
        assert "sections" not in data_keys


def test_moderation_unsupported_action_rejected(client: TestClient):
    """Unsupported actions (e.g. 'jail', 'demote') must be rejected with 422."""
    payload = {
        "action": "jail",
        "reason": "User was unruly.",
    }
    resp = client.post("/api/v1/generate/moderation/rewrite", json=payload)
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_moderation_empty_reason_rejected(client: TestClient):
    """Empty or whitespace reason must be rejected with 422."""
    payload = {
        "action": "warning",
        "reason": "   ",
    }
    resp = client.post("/api/v1/generate/moderation/rewrite", json=payload)
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
