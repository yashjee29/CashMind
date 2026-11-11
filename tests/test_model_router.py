"""
Tests for Model Router
Verifies task-based routing, temperature settings, and token limits.
"""

from app.core.providers.model_router import ModelRouter


def test_model_router_configs():
    router = ModelRouter()

    # Moderation task
    mod_cfg = router.get_config("moderation_rewrite")
    assert mod_cfg.task_name == "moderation_rewrite"
    assert mod_cfg.temperature <= 0.2  # Low temperature for strict factual rewriting
    assert mod_cfg.response_format == {"type": "json_object"}

    # Announcement generate
    gen_cfg = router.get_config("announcement_generate")
    assert gen_cfg.task_name == "announcement_generate"
    assert gen_cfg.temperature >= 0.5  # Engaging and motivational
    assert gen_cfg.response_format == {"type": "json_object"}

    # Announcement rewrite
    rew_cfg = router.get_config("announcement_rewrite")
    assert rew_cfg.task_name == "announcement_rewrite"
    assert rew_cfg.response_format == {"type": "json_object"}

    # Unknown task fallback
    unknown_cfg = router.get_config("unknown_task")
    assert unknown_cfg.task_name == "unknown_task"
    assert unknown_cfg.primary_model == mod_cfg.fallback_model
