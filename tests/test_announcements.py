"""
Tests for ICAI Announcement Generator and Rewriter
Verifies generate, rewrite, motivational tone, structured sections, and response envelopes.
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.core.providers.groq_provider import get_groq_provider


def test_announcement_generate_endpoint(client: TestClient):
    """Verifies that POST /api/v1/generate/announcements/generate produces structured announcement."""
    mock_announcement = {
        "type": "icai_announcement",
        "title": "Your Consistency Builds Your Future",
        "subtitle": "Daily CA Motivation",
        "introduction": "Every chapter you complete brings you one step closer to becoming a Chartered Accountant.",
        "sections": [
            {
                "heading": "Today's Study Focus",
                "icon": "target",
                "content": "Focus on high-weightage accounting standards and revise multiple-choice questions.",
                "items": [
                    "Complete at least 3 practice questions.",
                    "Review revision test papers.",
                    "Take regular 5-minute study breaks.",
                ],
            }
        ],
        "links": [
            {
                "label": "Study Portal",
                "url": "https://icai.org/bos",
                "icon": "book-open",
            }
        ],
        "closing_message": "Stay disciplined and trust your preparation. Keep moving forward!",
        "footer": "ICAI Study Community",
    }

    mock_llm_result = {
        "content": '{"dummy": true}',
        "parsed_json": mock_announcement,
        "model": "llama-3.3-70b-versatile",
        "provider": "groq",
    }

    with patch.object(
        get_groq_provider(), "generate_completion", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = mock_llm_result

        payload = {
            "operation": "generate",
            "topic": "Daily study targets",
            "instructions": "Motivate CA Intermediate students preparing for upcoming exams.",
            "tone": "motivational",
            "links": [
                {
                    "label": "Study Portal",
                    "url": "https://icai.org/bos",
                    "icon": "book-open",
                }
            ],
            "available_icons": ["target", "book-open", "graduation-cap"],
        }

        resp = client.post("/api/v1/generate/announcements/generate", json=payload)
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is True
        data = body["data"]
        assert data["type"] == "icai_announcement"
        assert data["title"] == "Your Consistency Builds Your Future"
        assert len(data["sections"]) == 1
        assert data["sections"][0]["heading"] == "Today's Study Focus"
        assert data["sections"][0]["icon"] == "target"
        assert len(data["sections"][0]["items"]) == 3
        assert len(data["links"]) == 1
        assert data["links"][0]["url"] == "https://icai.org/bos"
        assert data["closing_message"] is not None
        assert data["footer"] == "ICAI Study Community"


def test_announcement_rewrite_endpoint(client: TestClient):
    """Verifies that POST /api/v1/generate/announcements/rewrite restructures raw text."""
    raw_draft = (
        "Guys registration for mock test series starts on 15th Nov. "
        "Make sure to register before 5 PM at https://icai.org/mts."
    )

    mock_structured = {
        "type": "icai_announcement",
        "title": "ICAI Mock Test Series Registration Open",
        "subtitle": "Important Examination Notice",
        "introduction": "Test series are vital for building speed and accuracy ahead of the main exams.",
        "sections": [
            {
                "heading": "Registration Details",
                "icon": "calendar",
                "content": "Registration commences on 15th November. Please complete your registration before 5:00 PM.",
                "items": [
                    "Registration window opens: 15th November",
                    "Strict deadline: 5:00 PM IST",
                ],
            }
        ],
        "links": [
            {
                "label": "Register Here",
                "url": "https://icai.org/mts",
                "icon": "clipboard-list",
            }
        ],
        "closing_message": "Test your knowledge early so you can excel on exam day!",
        "footer": "ICAI Study Community",
    }

    mock_llm_result = {
        "content": '{"dummy": true}',
        "parsed_json": mock_structured,
        "model": "llama-3.3-70b-versatile",
        "provider": "groq",
    }

    with patch.object(
        get_groq_provider(), "generate_completion", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = mock_llm_result

        payload = {
            "operation": "rewrite",
            "existing_content": raw_draft,
            "instructions": "Make it clear and structured.",
            "links": [
                {
                    "label": "Register Here",
                    "url": "https://icai.org/mts",
                }
            ],
            "available_icons": ["calendar", "clipboard-list"],
        }

        resp = client.post("/api/v1/generate/announcements/rewrite", json=payload)
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is True
        assert body["data"]["title"] == "ICAI Mock Test Series Registration Open"
        assert body["data"]["links"][0]["url"] == "https://icai.org/mts"
        assert body["data"]["sections"][0]["icon"] == "calendar"


def test_announcement_generate_requires_topic_or_instructions(client: TestClient):
    """Missing both topic and instructions must fail with 422."""
    payload = {
        "operation": "generate",
        "topic": "   ",
        "instructions": "   ",
    }
    resp = client.post("/api/v1/generate/announcements/generate", json=payload)
    assert resp.status_code == 422


def test_announcement_rewrite_requires_existing_content(client: TestClient):
    """Empty existing_content must fail with 422."""
    payload = {
        "operation": "rewrite",
        "existing_content": "   ",
    }
    resp = client.post("/api/v1/generate/announcements/rewrite", json=payload)
    assert resp.status_code == 422


def test_announcement_craft_post_endpoint(client: TestClient):
    """Verifies that POST /api/v1/generate/announcements/craft-post generates a complete motivational Discord post."""
    mock_post_json = {
        "headline": "🎓 **CA Results Announcement – September 2026** 🎉",
        "content": "🎓 **CA Results Announcement – September 2026** 🎉\n\n@Foundation @Inter @Final\n\nThe results have been declared!\n\n🔗 **Check Your Results:**\nhttps://caresults.icai.org",
        "summary": "CA September 2026 examination results declared.",
    }

    mock_llm_result = {
        "content": '{"dummy": true}',
        "parsed_json": mock_post_json,
        "model": "openai/gpt-oss-120b",
        "provider": "groq",
    }

    with patch.object(
        get_groq_provider(), "generate_completion", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = mock_llm_result

        payload = {
            "title": "Results of CA Intermediate September 2026 Declared",
            "url": "https://caresults.icai.org",
            "roles": ["@Foundation", "@Inter", "@Final"],
            "custom_emojis": {"bot_logo": "<:bot_logo:1560720049021657168>"},
        }

        resp = client.post("/api/v1/generate/announcements/craft-post", json=payload)
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is True
        assert body["data"]["headline"] == "🎓 **CA Results Announcement – September 2026** 🎉"
        assert "caresults.icai.org" in body["data"]["content"]
        assert body["data"]["summary"] == "CA September 2026 examination results declared."
