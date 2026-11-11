"""
CashMind Structured Logging
Configures structured log output with correlation IDs and sensitive credential masking.
"""

import logging
import re
import sys
from contextvars import ContextVar
from typing import Optional

request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Pattern to detect Groq API keys (starts with gsk_) or generic long hex/alphanumeric tokens
GROQ_KEY_PATTERN = re.compile(r"gsk_[a-zA-Z0-9_-]{20,}", re.IGNORECASE)
BEARER_PATTERN = re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{10,}", re.IGNORECASE)


class SensitiveDataFilter(logging.Filter):
    """Redacts API keys and auth tokens from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = GROQ_KEY_PATTERN.sub("[REDACTED_GROQ_KEY]", record.msg)
            record.msg = BEARER_PATTERN.sub("Bearer [REDACTED_TOKEN]", record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (GROQ_KEY_PATTERN.sub("[REDACTED_GROQ_KEY]", str(v)) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    GROQ_KEY_PATTERN.sub("[REDACTED_GROQ_KEY]", str(v)) if isinstance(v, str) else v
                    for v in record.args
                )
        return True


class RequestIdFilter(logging.Filter):
    """Injects current request ID into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        req_id = request_id_ctx.get()
        record.request_id = req_id if req_id else "-"
        return True


def setup_logging(debug: bool = False) -> logging.Logger:
    """Sets up root logger formatting and handlers."""
    log_level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [req:%(request_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())
    handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    # Suppress verbose third-party loggers
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    return logging.getLogger("cashmind")


logger = setup_logging()
