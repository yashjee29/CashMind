"""
Standard API Response Envelopes
Ensures consistent format across all CashMind endpoints.
"""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ResponseMetadata(BaseModel):
    """Metadata detailing the AI provider, model used, and request tracking."""

    model: str = Field(description="Actual model identifier used for generation")
    provider: str = Field(default="groq", description="LLM inference provider")
    prompt_version: Optional[str] = Field(default=None, description="Version of the prompt template used")


class SuccessResponse(BaseModel, Generic[DataT]):
    """Standard success response wrapper."""

    success: bool = True
    data: DataT
    metadata: ResponseMetadata


class ErrorDetail(BaseModel):
    """Structured error payload."""

    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""

    success: bool = False
    error: ErrorDetail
