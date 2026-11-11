"""
Shared Groq Provider Client
Central gateway for all Groq LLM inference in CashMind.
Integrates API key pooling, model routing, request scheduling, and structured response parsing.
"""

import json
from typing import Any, Dict, List, Optional
from groq import AsyncGroq, APIConnectionError, InternalServerError, RateLimitError as GroqRateLimitError, APIStatusError
from app.core.config import settings
from app.core.exceptions import OutputValidationError, ProviderError, QuotaExhaustedError, RateLimitError
from app.core.logging import logger
from app.core.providers.key_pool import ApiKeyPool
from app.core.providers.model_router import ModelRouter, TaskModelConfig
from app.core.providers.scheduler import RequestScheduler


class GroqProvider:
    """Unified Groq LLM provider service managing client sessions, keys, and routing."""

    def __init__(
        self,
        key_pool: Optional[ApiKeyPool] = None,
        model_router: Optional[ModelRouter] = None,
        scheduler: Optional[RequestScheduler] = None,
    ) -> None:
        self.key_pool = key_pool or ApiKeyPool(
            keys=settings.groq_keys_list,
            default_cooldown_seconds=settings.KEY_COOLDOWN_SECONDS,
        )
        self.model_router = model_router or ModelRouter()
        self.scheduler = scheduler or RequestScheduler()
        self._clients: Dict[str, AsyncGroq] = {}

    def _get_client(self, api_key: str) -> AsyncGroq:
        """Retrieves or creates a cached AsyncGroq instance for a given key."""
        if api_key not in self._clients:
            self._clients[api_key] = AsyncGroq(api_key=api_key, timeout=settings.GROQ_REQUEST_TIMEOUT_SECONDS)
        return self._clients[api_key]

    async def generate_completion(
        self,
        task: str,
        messages: List[Dict[str, str]],
        override_model: Optional[str] = None,
        response_format: Optional[Dict[str, str]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes chat completion with automatic API key rotation, model fallback,
        and structured JSON extraction.
        """
        task_config: TaskModelConfig = self.model_router.get_config(task)
        model_to_use = override_model or task_config.primary_model
        temp = temperature if temperature is not None else task_config.temperature
        tokens = max_tokens if max_tokens is not None else task_config.max_tokens
        fmt = response_format or task_config.response_format

        async def _call_groq() -> Dict[str, Any]:
            nonlocal model_to_use

            # 1. Fetch available key from the pool
            key_info = self.key_pool.get_key()
            client = self._get_client(key_info.key)

            try:
                kwargs: Dict[str, Any] = {
                    "model": model_to_use,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": tokens,
                }
                if fmt:
                    kwargs["response_format"] = fmt

                response = await client.chat.completions.create(**kwargs)
                self.key_pool.mark_success(key_info.key)

                content = response.choices[0].message.content or ""
                actual_model = response.model or model_to_use

                # Parse JSON if structured output was requested
                parsed_json = None
                if fmt and fmt.get("type") == "json_object":
                    try:
                        parsed_json = json.loads(content)
                    except json.JSONDecodeError as jde:
                        logger.error(f"Failed to decode JSON from Groq response: {content}")
                        raise OutputValidationError(
                            f"LLM response was not valid JSON: {str(jde)}",
                            details={"raw_content": content},
                        )

                return {
                    "content": content,
                    "parsed_json": parsed_json,
                    "model": actual_model,
                    "provider": "groq",
                }

            except GroqRateLimitError as rle:
                # Key hit rate limit, mark in pool and trigger retry with another key
                self.key_pool.mark_rate_limited(key_info.key)
                raise RateLimitError(f"Groq rate limit encountered: {str(rle)}")

            except APIStatusError as ase:
                # If 401/403, key is invalid
                if ase.status_code in (401, 403):
                    self.key_pool.mark_failure(key_info.key, is_fatal=True)
                    raise ProviderError(f"Groq authentication error: {ase.message}")

                # If 400 Bad Request and primary model failed, try fallback model
                if ase.status_code == 400 and model_to_use != task_config.fallback_model:
                    logger.warning(
                        f"Model '{model_to_use}' failed with 400. Falling back to '{task_config.fallback_model}'."
                    )
                    model_to_use = task_config.fallback_model
                    raise ProviderError(f"Primary model rejected request: {ase.message}")

                self.key_pool.mark_failure(key_info.key)
                raise ProviderError(f"Groq API error (status {ase.status_code}): {ase.message}")

            except (APIConnectionError, InternalServerError) as conn_err:
                self.key_pool.mark_failure(key_info.key)
                raise ProviderError(f"Groq network or service error: {str(conn_err)}")

        return await self.scheduler.execute(_call_groq, task_name=task)


# Global provider singleton
_groq_provider_instance: Optional[GroqProvider] = None


def get_groq_provider() -> GroqProvider:
    """Retrieves or initializes the global shared GroqProvider instance."""
    global _groq_provider_instance
    if _groq_provider_instance is None:
        _groq_provider_instance = GroqProvider()
    return _groq_provider_instance
