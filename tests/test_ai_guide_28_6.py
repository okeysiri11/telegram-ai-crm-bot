"""Tests — AI Guide (Sprint 28.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/platform-builder/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_platform_builder_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_ai_guide_functions():
    guide = platform_builder.academy_v2.guide
    assert guide.status()["ready"] is True
    assert len(guide.status()["functions"]) == 5

    explain = guide.explain_step(builder_id="vertical", step="Module Selection", level="beginner")
    assert "Module Selection" in explain["message"]

    recommend = guide.recommend_configuration(builder_id="vertical", draft={})
    assert recommend["suggestions"]

    answer = guide.answer(question="What is a Concierge?", builder_id="concierge")
    assert "Concierge" in answer["answer"] or "concierge" in answer["answer"].lower()

    improvements = guide.suggest_improvements(draft={"modules": ["crm"]})
    assert improvements["improvements"]

    warnings = guide.warn_missing(draft={"name": "X"})
    assert warnings["has_warnings"] is True
    assert "Modules" in warnings["missing"]

    coach = guide.coach(
        builder_id="vertical",
        step="Dashboard",
        question="What is best practice?",
        draft={"name": "Clinic", "modules": ["crm"]},
        level="intermediate",
    )
    assert coach["ready"] is True
    assert "answer" in coach
    assert coach["warnings"]["function"] == "Warn about missing components"


@pytest.mark.asyncio
async def test_api_ai_guide(client):
    coach = await client.post(
        f"{PREFIX}/academy/v2/guide",
        json={
            "builder_id": "ai",
            "step": "Profession",
            "level": "beginner",
            "draft": {"name": "Ava"},
        },
    )
    assert coach.status == 200
    body = await coach.json()
    assert body["explain"]["function"] == "Explain current step"

    ask = await client.post(
        f"{PREFIX}/academy/v2/guide/ask",
        json={"question": "Which modules are best?", "builder_id": "vertical"},
    )
    assert ask.status == 200
    assert "answer" in await ask.json()


def test_docs_ai_guide_28_6():
    assert (ROOT / "docs" / "AI_GUIDE.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "guide" / "README.md").exists()
    docs = (ROOT / "docs" / "AI_GUIDE.md").read_text()
    for key in ("Explain current step", "Recommend configuration", "Warn about missing"):
        assert key in docs
