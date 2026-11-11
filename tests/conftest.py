"""
Pytest Fixtures and Mock Setup for CashMind Test Suite
Provides mocked Groq client responses, test FastAPI client, and sample payloads.
"""

from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.providers.groq_provider import GroqProvider, get_groq_provider
from app.core.providers.key_pool import ApiKeyPool
from app.core.providers.model_router import ModelRouter
from app.core.providers.scheduler import RequestScheduler
from app.main import app
from app.modules.generate.announcements.generator import AnnouncementGenerator
from app.modules.generate.announcements.rewriter import AnnouncementRewriter
from app.modules.generate.announcements.service import AnnouncementService
from app.modules.generate.moderation.rewriter import ModerationRewriter
from app.modules.generate.moderation.service import ModerationService


class MockGroqChatCompletions:
    """Mock for client.chat.completions."""

    def __init__(self, response_data: Dict[str, Any], model_name: str = "llama-3.3-70b-versatile"):
        self.response_data = response_data
        self.model_name = model_name

    async def create(self, **kwargs: Any) -> Any:
        import json

        content = json.dumps(self.response_data)
        choice_mock = MagicMock()
        choice_mock.message.content = content

        response_mock = MagicMock()
        response_mock.choices = [choice_mock]
        response_mock.model = self.model_name
        return response_mock


@pytest.fixture
def test_key_pool() -> ApiKeyPool:
    """Returns an isolated key pool with test keys."""
    return ApiKeyPool(
        keys=["gsk_test_key_1111111111111111111111", "gsk_test_key_2222222222222222222222"],
        default_cooldown_seconds=1.0,
    )


@pytest.fixture
def mock_groq_provider(test_key_pool: ApiKeyPool) -> GroqProvider:
    """Returns a GroqProvider instance with mock client dispatch."""
    provider = GroqProvider(
        key_pool=test_key_pool,
        model_router=ModelRouter(),
        scheduler=RequestScheduler(max_concurrency=5, timeout_seconds=10.0, max_retries=2),
    )
    return provider


@pytest.fixture
def client() -> TestClient:
    """Standard FastAPI TestClient."""
    return TestClient(app)
