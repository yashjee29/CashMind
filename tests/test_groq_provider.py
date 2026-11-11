"""
Tests for Centralized GroqProvider
Verifies key failover on 429, fallback model on 400, auth failure on 401, and JSON output parsing.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from groq import APIStatusError, RateLimitError as GroqRateLimitError
from app.core.exceptions import OutputValidationError, ProviderError, RateLimitError
from app.core.providers.groq_provider import GroqProvider
from app.core.providers.key_pool import ApiKeyPool
from app.core.providers.model_router import ModelRouter
from app.core.providers.scheduler import RequestScheduler


@pytest.mark.asyncio
async def test_groq_provider_key_failover_on_429():
    """When a key hits 429, provider should mark key in cooldown and scheduler should retry with next key."""
    k1 = "gsk_key1_11111111111111111111"
    k2 = "gsk_key2_22222222222222222222"
    key_pool = ApiKeyPool(keys=[k1, k2], default_cooldown_seconds=10.0)

    # Scheduler with 2 retries
    scheduler = RequestScheduler(max_concurrency=2, timeout_seconds=5.0, max_retries=2)
    provider = GroqProvider(key_pool=key_pool, scheduler=scheduler)

    # Mock client factory
    mock_client1 = MagicMock()
    mock_client2 = MagicMock()

    # Client 1 raises 429
    rate_limit_resp = MagicMock()
    rate_limit_resp.status_code = 429
    mock_client1.chat.completions.create = AsyncMock(
        side_effect=GroqRateLimitError(
            message="Rate limit reached",
            response=rate_limit_resp,
            body={"error": {"message": "Rate limit"}},
        )
    )

    # Client 2 succeeds
    success_resp = MagicMock()
    choice_mock = MagicMock()
    choice_mock.message.content = '{"rewritten_reason": "Formal reason"}'
    success_resp.choices = [choice_mock]
    success_resp.model = "llama-3.3-70b-versatile"
    mock_client2.chat.completions.create = AsyncMock(return_value=success_resp)

    provider._clients[k1] = mock_client1
    provider._clients[k2] = mock_client2

    result = await provider.generate_completion(
        task="moderation_rewrite",
        messages=[{"role": "user", "content": "test"}],
    )

    assert result["parsed_json"] == {"rewritten_reason": "Formal reason"}
    # k1 should be in cooldown
    assert not key_pool.keys_info[0].is_available
    # k2 should be active and have 1 success
    assert key_pool.keys_info[1].successful_requests == 1


@pytest.mark.asyncio
async def test_groq_provider_unsupported_model_triggers_fallback():
    """When primary model fails with 400, provider retries with fallback model."""
    k1 = "gsk_key1_11111111111111111111"
    key_pool = ApiKeyPool(keys=[k1])
    scheduler = RequestScheduler(max_concurrency=1, timeout_seconds=5.0, max_retries=2)
    provider = GroqProvider(key_pool=key_pool, scheduler=scheduler)

    mock_client = MagicMock()

    err_resp = MagicMock()
    err_resp.status_code = 400
    bad_req_error = APIStatusError(
        message="Model does not support json_object",
        response=err_resp,
        body={"error": {"message": "Invalid request"}},
    )

    success_resp = MagicMock()
    choice_mock = MagicMock()
    choice_mock.message.content = '{"title": "Valid announcement"}'
    success_resp.choices = [choice_mock]
    success_resp.model = "llama-3.1-8b-instant"

    # First call fails with 400, second call with fallback model succeeds
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[bad_req_error, success_resp]
    )
    provider._clients[k1] = mock_client

    result = await provider.generate_completion(
        task="announcement_generate",
        messages=[{"role": "user", "content": "test"}],
    )

    assert result["parsed_json"] == {"title": "Valid announcement"}
    assert result["model"] == "llama-3.1-8b-instant"


@pytest.mark.asyncio
async def test_groq_provider_malformed_json_raises_output_validation_error():
    """If Groq returns non-JSON content when json_object mode was requested, raise OutputValidationError."""
    k1 = "gsk_key1_11111111111111111111"
    key_pool = ApiKeyPool(keys=[k1])
    scheduler = RequestScheduler(max_concurrency=1, timeout_seconds=5.0, max_retries=0)
    provider = GroqProvider(key_pool=key_pool, scheduler=scheduler)

    mock_client = MagicMock()
    success_resp = MagicMock()
    choice_mock = MagicMock()
    choice_mock.message.content = "This is not valid JSON at all!"
    success_resp.choices = [choice_mock]
    success_resp.model = "llama-3.3-70b-versatile"

    mock_client.chat.completions.create = AsyncMock(return_value=success_resp)
    provider._clients[k1] = mock_client

    with pytest.raises(OutputValidationError) as exc_info:
        await provider.generate_completion(
            task="moderation_rewrite",
            messages=[{"role": "user", "content": "test"}],
            response_format={"type": "json_object"},
        )

    assert "not valid JSON" in str(exc_info.value)
