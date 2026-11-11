"""
Tests for Internal Service Authentication
Verifies API key enforcement and unauthorized access rejection.
"""

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.providers.groq_provider import get_groq_provider
from app.main import app


def test_auth_enforcement_when_configured():
    """When CASHMIND_API_KEY is configured, invalid or missing credentials must yield 401."""
    with patch.object(settings, "CASHMIND_API_KEY", "secret_service_key_xyz"):
        test_client = TestClient(app)

        # 1. Missing header -> 401
        resp = test_client.post(
            "/api/v1/generate/moderation/rewrite",
            json={"action": "warning", "reason": "Disruptive behavior"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AUTHENTICATION_FAILED"

        # 2. Invalid header -> 401
        resp = test_client.post(
            "/api/v1/generate/moderation/rewrite",
            headers={"X-API-Key": "wrong_key"},
            json={"action": "warning", "reason": "Disruptive behavior"},
        )
        assert resp.status_code == 401

        # 3. Valid X-API-Key -> 200 (with mocked provider)
        with patch.object(
            get_groq_provider(), "generate_completion", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = {
                "content": '{"rewritten_reason": "Formal warning reason."}',
                "parsed_json": {"rewritten_reason": "Formal warning reason."},
                "model": "llama-3.3-70b-versatile",
                "provider": "groq",
            }

            resp = test_client.post(
                "/api/v1/generate/moderation/rewrite",
                headers={"X-API-Key": "secret_service_key_xyz"},
                json={"action": "warning", "reason": "Disruptive behavior"},
            )
            assert resp.status_code == 200
            assert resp.json()["success"] is True

        # 4. Valid Bearer Token in Authorization header -> 200
        with patch.object(
            get_groq_provider(), "generate_completion", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = {
                "content": '{"rewritten_reason": "Formal warning reason."}',
                "parsed_json": {"rewritten_reason": "Formal warning reason."},
                "model": "llama-3.3-70b-versatile",
                "provider": "groq",
            }

            resp = test_client.post(
                "/api/v1/generate/moderation/rewrite",
                headers={"Authorization": "Bearer secret_service_key_xyz"},
                json={"action": "warning", "reason": "Disruptive behavior"},
            )
            assert resp.status_code == 200
            assert resp.json()["success"] is True
