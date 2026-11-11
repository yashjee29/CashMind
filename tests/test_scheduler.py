"""
Tests for Centralized Request Scheduler
Verifies concurrency limits, timeouts, and retry logic.
"""

import asyncio
import pytest
from app.core.exceptions import ProviderError
from app.core.providers.scheduler import RequestScheduler


@pytest.mark.asyncio
async def test_scheduler_concurrency_limiting():
    """Ensures no more than max_concurrency operations run concurrently."""
    scheduler = RequestScheduler(max_concurrency=2, timeout_seconds=5.0, max_retries=1)
    running = 0
    max_observed = 0

    async def _op():
        nonlocal running, max_observed
        running += 1
        max_observed = max(max_observed, running)
        await asyncio.sleep(0.05)
        running -= 1
        return "ok"

    tasks = [scheduler.execute(_op) for _ in range(5)]
    results = await asyncio.gather(*tasks)

    assert results == ["ok"] * 5
    assert max_observed <= 2


@pytest.mark.asyncio
async def test_scheduler_timeout():
    """Operation exceeding timeout should raise ProviderError."""
    scheduler = RequestScheduler(max_concurrency=1, timeout_seconds=0.1, max_retries=0)

    async def _slow_op():
        await asyncio.sleep(0.3)
        return "late"

    with pytest.raises(ProviderError) as exc_info:
        await scheduler.execute(_slow_op, task_name="slow_task")

    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_scheduler_retries_transient_failure():
    """Failing operation should retry up to max_retries and succeed if transient."""
    scheduler = RequestScheduler(max_concurrency=1, timeout_seconds=5.0, max_retries=2)
    attempts = 0

    async def _eventually_successful_op():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ProviderError("Temporary glitch")
        return "recovered"

    result = await scheduler.execute(_eventually_successful_op, task_name="retry_task")
    assert result == "recovered"
    assert attempts == 2
