"""
Model Routing and Task Profiles
Maps generative operations to appropriate Groq models, token limits, and parameters.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from app.core.config import settings


@dataclass
class TaskModelConfig:
    """Configuration profile for a specific generative task."""

    task_name: str
    primary_model: str
    fallback_model: str
    temperature: float
    max_tokens: int
    response_format: Optional[Dict[str, str]] = None


class ModelRouter:
    """Routes requests based on task type with fallback capability."""

    def __init__(self) -> None:
        self._profiles: Dict[str, TaskModelConfig] = {
            "moderation_rewrite": TaskModelConfig(
                task_name="moderation_rewrite",
                primary_model=settings.GROQ_MODEL_MODERATION,
                fallback_model=settings.GROQ_FALLBACK_MODEL,
                temperature=0.2,  # Controlled low temperature for deterministic, factual rewriting in JSON format
                max_tokens=600,
                response_format={"type": "json_object"},
            ),
            "announcement_generate": TaskModelConfig(
                task_name="announcement_generate",
                primary_model=settings.GROQ_MODEL_ANNOUNCEMENT_GEN,
                fallback_model=settings.GROQ_FALLBACK_MODEL,
                temperature=0.7,  # Engaging, motivational tone
                max_tokens=2048,
                response_format={"type": "json_object"},
            ),
            "announcement_rewrite": TaskModelConfig(
                task_name="announcement_rewrite",
                primary_model=settings.GROQ_MODEL_ANNOUNCEMENT_REW,
                fallback_model=settings.GROQ_FALLBACK_MODEL,
                temperature=0.4,  # Polished and engaging while tightly preserving facts
                max_tokens=2048,
                response_format={"type": "json_object"},
            ),
            "announcement_craft_post": TaskModelConfig(
                task_name="announcement_craft_post",
                primary_model=settings.GROQ_MODEL_ANNOUNCEMENT_GEN,
                fallback_model=settings.GROQ_FALLBACK_MODEL,
                temperature=0.75,  # Dynamic variety and fresh motivational templates every run
                max_tokens=2048,
                response_format={"type": "json_object"},
            ),
        }

    def get_config(self, task: str) -> TaskModelConfig:
        """Retrieves task profile or returns default fallback configuration."""
        if task in self._profiles:
            return self._profiles[task]
        return TaskModelConfig(
            task_name=task,
            primary_model=settings.GROQ_FALLBACK_MODEL,
            fallback_model=settings.GROQ_FALLBACK_MODEL,
            temperature=0.5,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

    def get_registered_models(self) -> Dict[str, str]:
        """Provides configured models for health diagnostics."""
        return {
            "moderation_rewrite": settings.GROQ_MODEL_MODERATION,
            "announcement_generate": settings.GROQ_MODEL_ANNOUNCEMENT_GEN,
            "announcement_rewrite": settings.GROQ_MODEL_ANNOUNCEMENT_REW,
            "fallback": settings.GROQ_FALLBACK_MODEL,
        }
