"""
API Key Pooling and Quota Management
Maintains health, cooldowns, and load balancing across multiple Groq API keys.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from app.core.exceptions import QuotaExhaustedError
from app.core.logging import logger


@dataclass
class ApiKeyInfo:
    """Tracks state and usage statistics for a single API key."""

    key: str
    healthy: bool = True
    cooldown_until: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limit_hits: int = 0
    last_used_at: float = 0.0

    @property
    def is_available(self) -> bool:
        """Key is ready if healthy and not in cooldown."""
        return self.healthy and time.time() >= self.cooldown_until

    @property
    def masked_key(self) -> str:
        """Returns safe preview for logging (e.g. gsk_...1234)."""
        if len(self.key) <= 8:
            return "***"
        return f"{self.key[:6]}...{self.key[-4:]}"


class ApiKeyPool:
    """Manages an active pool of Groq API keys with automatic failover and cooldown."""

    def __init__(self, keys: List[str], default_cooldown_seconds: float = 60.0) -> None:
        self.default_cooldown = default_cooldown_seconds
        self.keys_info: List[ApiKeyInfo] = [ApiKeyInfo(key=k) for k in keys if k]
        self._current_index = 0

    def add_key(self, key: str) -> None:
        """Dynamically registers an API key into the pool."""
        clean_key = key.strip()
        if clean_key and not any(info.key == clean_key for info in self.keys_info):
            self.keys_info.append(ApiKeyInfo(key=clean_key))

    def get_key(self) -> ApiKeyInfo:
        """
        Retrieves the next available healthy key via round-robin.
        Raises QuotaExhaustedError if no keys are currently usable.
        """
        if not self.keys_info:
            raise QuotaExhaustedError("No Groq API keys are configured in CashMind.")

        total = len(self.keys_info)
        now = time.time()

        # 1. Round-robin scan for an immediately available key
        for i in range(total):
            idx = (self._current_index + i) % total
            candidate = self.keys_info[idx]
            if candidate.is_available:
                self._current_index = (idx + 1) % total
                candidate.total_requests += 1
                candidate.last_used_at = now
                return candidate

        # 2. Check if all keys are currently in cooldown vs permanently failed
        healthy_keys = [k for k in self.keys_info if k.healthy]
        if not healthy_keys:
            raise QuotaExhaustedError("All Groq API keys are permanently unhealthy.")

        min_cooldown = min(k.cooldown_until for k in healthy_keys)
        wait_seconds = max(0.1, min_cooldown - now)
        raise QuotaExhaustedError(
            f"All Groq API keys are currently rate-limited or in cooldown. Shortest retry in {wait_seconds:.1f}s."
        )

    def mark_rate_limited(self, key_str: str, retry_after: Optional[float] = None) -> None:
        """Places a key in temporary cooldown following HTTP 429."""
        cooldown = retry_after if retry_after and retry_after > 0 else self.default_cooldown
        until = time.time() + cooldown
        for info in self.keys_info:
            if info.key == key_str:
                info.rate_limit_hits += 1
                info.failed_requests += 1
                info.cooldown_until = until
                logger.warning(
                    f"Groq API key {info.masked_key} placed in cooldown for {cooldown:.1f}s due to rate limit."
                )
                break

    def mark_failure(self, key_str: str, is_fatal: bool = False) -> None:
        """Records failure and optionally deactivates invalid key."""
        for info in self.keys_info:
            if info.key == key_str:
                info.failed_requests += 1
                if is_fatal:
                    info.healthy = False
                    logger.error(f"Groq API key {info.masked_key} marked PERMANENTLY UNHEALTHY (invalid key).")
                break

    def mark_success(self, key_str: str) -> None:
        """Records successful API execution."""
        for info in self.keys_info:
            if info.key == key_str:
                info.successful_requests += 1
                break

    def get_status(self) -> Dict[str, object]:
        """Provides sanitized pool health statistics without revealing secrets."""
        now = time.time()
        total = len(self.keys_info)
        healthy = sum(1 for k in self.keys_info if k.healthy)
        in_cooldown = sum(1 for k in self.keys_info if k.healthy and k.cooldown_until > now)
        ready = sum(1 for k in self.keys_info if k.is_available)

        return {
            "total_keys": total,
            "healthy_keys": healthy,
            "ready_keys": ready,
            "in_cooldown_keys": in_cooldown,
            "pool_ready": ready > 0,
        }
