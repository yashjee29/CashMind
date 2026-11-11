"""
Tests for API Key Pooling and Quota Management
Verifies round-robin rotation, 429 cooldowns, error tracking, and quota exhaustion.
"""

import time
import pytest
from app.core.exceptions import QuotaExhaustedError
from app.core.providers.key_pool import ApiKeyPool


def test_empty_key_pool_raises():
    """An empty key pool should raise QuotaExhaustedError."""
    pool = ApiKeyPool(keys=[])
    with pytest.raises(QuotaExhaustedError) as exc_info:
        pool.get_key()
    assert "No Groq API keys" in str(exc_info.value)


def test_round_robin_rotation():
    """Multiple keys should rotate in round-robin sequence."""
    k1 = "gsk_key1_11111111111111111111"
    k2 = "gsk_key2_22222222222222222222"
    pool = ApiKeyPool(keys=[k1, k2])

    first = pool.get_key()
    second = pool.get_key()
    third = pool.get_key()

    assert first.key == k1
    assert second.key == k2
    assert third.key == k1


def test_rate_limit_cooldown_and_failover():
    """Rate limited key should enter cooldown; pool should failover to next key."""
    k1 = "gsk_key1_11111111111111111111"
    k2 = "gsk_key2_22222222222222222222"
    pool = ApiKeyPool(keys=[k1, k2], default_cooldown_seconds=0.2)

    key_info = pool.get_key()
    assert key_info.key == k1

    # Mark k1 as rate-limited
    pool.mark_rate_limited(k1, retry_after=0.2)

    # Next call should immediately return k2 (not k1)
    next_info = pool.get_key()
    assert next_info.key == k2

    # If k2 is also rate-limited:
    pool.mark_rate_limited(k2, retry_after=0.2)

    # Now all keys are in cooldown; should raise QuotaExhaustedError
    with pytest.raises(QuotaExhaustedError):
        pool.get_key()

    # Wait for cooldown to expire
    time.sleep(0.25)

    # Key should be available again
    recovered = pool.get_key()
    assert recovered.key in (k1, k2)


def test_permanent_failure():
    """Fatal auth errors (401/403) should mark key permanently unhealthy."""
    k1 = "gsk_invalid_11111111111111111111"
    k2 = "gsk_valid_22222222222222222222"
    pool = ApiKeyPool(keys=[k1, k2])

    pool.mark_failure(k1, is_fatal=True)

    # k1 should never be returned again
    for _ in range(3):
        assert pool.get_key().key == k2


def test_sanitized_status():
    """Pool status metrics should never expose raw keys."""
    k1 = "gsk_super_secret_key_1111111111"
    pool = ApiKeyPool(keys=[k1])

    status = pool.get_status()
    assert status["total_keys"] == 1
    assert status["healthy_keys"] == 1
    assert status["ready_keys"] == 1
    assert "gsk_super_secret_key" not in str(status)
