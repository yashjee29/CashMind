"""
Centralized Request Scheduling and Rate Limit Management
Implements concurrency control, timeout enforcement, and resilient retry logic with jitter.
"""

import asyncio
import random
from typing import Awaitable, Callable, TypeVar
from app.core.config import settings
from app.core.exceptions import OutputValidationError, ProviderError, RateLimitError
from app.core.logging import logger

T = TypeVar("T")


class RequestScheduler:
    """Schedules requests under strict concurrency limits with exponential backoff retries."""

    def __init__(
        self,
        max_concurrency: int = settings.GROQ_MAX_CONCURRENCY,
        timeout_seconds: float = settings.GROQ_REQUEST_TIMEOUT_SECONDS,
        max_retries: int = settings.GROQ_MAX_RETRIES,
    ) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        task_name: str = "llm_request",
    ) -> T:
        """
        Executes an asynchronous operation guarded by concurrency limits and retry policies.
        Retries on transient network errors or recoverable provider faults.
        """
        async with self.semaphore:
            last_exception: Exception | None = None
            delay = 0.5

            for attempt in range(self.max_retries + 1):
                try:
                    return await asyncio.wait_for(operation(), timeout=self.timeout_seconds)
                except OutputValidationError:
                    # Output validation errors should bubble up immediately without retry
                    raise
                except asyncio.TimeoutError as te:
                    last_exception = ProviderError(
                        f"Request timed out after {self.timeout_seconds}s for task '{task_name}'."
                    )
                    logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries + 1} for '{task_name}'.")
                except RateLimitError as rle:
                    last_exception = rle
                    logger.warning(
                        f"Rate limit on attempt {attempt + 1}/{self.max_retries + 1} for '{task_name}': {rle.message}"
                    )
                except ProviderError as pe:
                    last_exception = pe
                    logger.warning(
                        f"Provider error on attempt {attempt + 1}/{self.max_retries + 1} for '{task_name}': {pe.message}"
                    )
                except Exception as e:
                    last_exception = ProviderError(f"Unexpected provider error: {str(e)}")
                    logger.warning(
                        f"Exception on attempt {attempt + 1}/{self.max_retries + 1} for '{task_name}': {str(e)}"
                    )

                if attempt < self.max_retries:
                    # Exponential backoff with random jitter (+/- 20%)
                    jitter = delay * random.uniform(0.8, 1.2)
                    logger.info(f"Retrying '{task_name}' in {jitter:.2f}s (attempt {attempt + 2})...")
                    await asyncio.sleep(jitter)
                    delay *= 2.0

            if last_exception:
                raise last_exception
            raise ProviderError(f"Request failed after {self.max_retries + 1} attempts.")
