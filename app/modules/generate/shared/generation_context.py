"""
Generation Context Helpers
Carries request-scoped context across generative pipelines.
"""

from dataclasses import dataclass, field
import time
from typing import Optional


@dataclass
class GenerationContext:
    """Carries timing, correlation ID, and module metadata for a generation invocation."""

    request_id: str
    task_name: str
    start_time: float = field(default_factory=time.time)
    selected_model: Optional[str] = None

    @property
    def elapsed_ms(self) -> float:
        return (time.time() - self.start_time) * 1000.0
