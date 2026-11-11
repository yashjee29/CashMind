"""
CashMind Custom Exception Hierarchy
Provides typed domain errors with associated HTTP status codes and machine-readable error codes.
"""

from typing import Any, Optional


class CashMindError(Exception):
    """Base exception for all CashMind domain errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class AuthenticationError(CashMindError):
    """Raised when request lacks valid internal service credentials."""

    status_code: int = 401
    error_code: str = "AUTHENTICATION_FAILED"


class ValidationError(CashMindError):
    """Raised when user input violates validation constraints."""

    status_code: int = 422
    error_code: str = "VALIDATION_ERROR"


class RateLimitError(CashMindError):
    """Raised when provider or internal service rate limits are exceeded."""

    status_code: int = 429
    error_code: str = "RATE_LIMIT_EXCEEDED"


class QuotaExhaustedError(CashMindError):
    """Raised when all API keys in the pool have exhausted their quotas."""

    status_code: int = 503
    error_code: str = "QUOTA_EXHAUSTED"


class ProviderError(CashMindError):
    """Raised when the LLM provider fails after retries."""

    status_code: int = 502
    error_code: str = "PROVIDER_ERROR"


class OutputValidationError(CashMindError):
    """Raised when LLM returns malformed or unverifiable structured output."""

    status_code: int = 502
    error_code: str = "INVALID_MODEL_OUTPUT"
