"""
Tests for CashMind Health Endpoints
Verifies root /health and /api/v1/generate/health.
"""

from fastapi.testclient import TestClient


def test_root_health(client: TestClient) -> None:
    """Verifies that GET /health returns 200 and basic service info."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "cashmind"


def test_generate_health(client: TestClient) -> None:
    """Verifies that GET /api/v1/generate/health returns pool and model readiness."""
    resp = client.get("/api/v1/generate/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "cashmind-generate"
    assert data["provider"] == "groq"
    assert "pool" in data
    assert "models" in data
    # Ensure no secrets or API keys are exposed
    raw_str = resp.text
    assert "gsk_" not in raw_str
