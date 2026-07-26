"""Tests — Builder Academy 2.0 (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.academy_v2.catalogs import EXPERIENCE_LEVELS, WIZARD_STEPS


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


def test_academy_v2_ready_and_levels():
    health = platform_builder.health()
    assert health["application_version"] == "1.18.0"
    assert health["sprint"] == "29.11"
    assert health["academy_2_ready"] is True
    assert health["ai_guide_ready"] is True
    assert health["recommendation_engine_ready"] is True
    assert health["progress_tracking_ready"] is True
    assert health["engines"]["builder_academy"] == "2.0"
    assert health["engines"]["ai_guide"] == "1.0"

    catalog = platform_builder.academy_v2.catalog()
    assert catalog["operational"] is True
    assert catalog["version"] == "2.0.0"
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert len(EXPERIENCE_LEVELS) == 4

    adapted = platform_builder.academy_v2.adapt_behavior("beginner")
    assert adapted["adaptations"]["show_walkthrough"] is True
    expert = platform_builder.academy_v2.adapt_behavior("expert")
    assert expert["builder_behavior"]["coach_visible"] is False

    help_bits = platform_builder.academy_v2.contextual_help("modules", "vertical")
    for key in (
        "explanation",
        "business_purpose",
        "example",
        "best_practice",
        "common_mistakes",
        "more_information",
    ):
        assert key in help_bits


def test_recommendations_analysis_progress_create():
    recs = platform_builder.academy_v2.recommendations.recommend(
        builder_id="vertical", industry="medical"
    )
    assert recs["items"]
    assert any(i["type"] == "ai_specialists" for i in recs["items"])

    analysis = platform_builder.academy_v2.live_analysis(
        {"name": "Clinic", "modules": ["crm"]}, builder_id="vertical"
    )
    assert "strengths" in analysis
    assert "missing_components" in analysis
    assert analysis["readiness_score"] >= 0

    impact = platform_builder.academy_v2.impact("crm", "CRM")
    assert "business_value" in impact
    assert "estimated_impact" in impact

    learning = platform_builder.academy_v2.interactive_learning("owner")
    assert "learning_path" in learning
    assert "tips" in learning

    session = platform_builder.academy_v2.start_session(user_id="owner")
    platform_builder.academy_v2.update_session(
        session["session_id"],
        {
            "draft": {
                "experience_level": "intermediate",
                "builder_id": "vertical",
                "industry": "medical",
                "completed_lessons": ["intro", "help", "guide"],
                "draft_snapshot": {
                    "name": "Bright Dental",
                    "modules": ["crm", "knowledge_base", "analytics"],
                    "ai_mode": "connect_existing",
                    "knowledge_topics": ["SOPs"],
                    "dashboard_widgets": ["kpi_overview"],
                },
            }
        },
    )
    summary = platform_builder.academy_v2.summary(session["session_id"])
    assert summary["title"] == "Academy 2.0 Summary"
    assert "business_readiness" in summary

    created = platform_builder.academy_v2.create(session["session_id"])
    assert created["ok"] is True
    assert created["progress"]["experience_level"] in (
        "beginner",
        "intermediate",
        "advanced",
        "expert",
    )
    assert created["recommendations"]["items"]
    assert created["learning_state"]["learning_state_id"]
    assert "first_builder" in created["progress"]["achievements"]


@pytest.mark.asyncio
async def test_api_academy_v2(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["academy_2_ready"] is True
    assert body["application_version"] == "1.18.0"

    catalog = await client.get(f"{PREFIX}/academy/v2/catalog")
    assert catalog.status == 200

    level = await client.get(f"{PREFIX}/academy/v2/levels/beginner")
    assert level.status == 200

    session = await client.post(f"{PREFIX}/academy/v2/sessions", json={"user_id": "owner"})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    patch = await client.patch(
        f"{PREFIX}/academy/v2/sessions/{sid}",
        json={"draft": {"experience_level": "beginner", "builder_id": "ai"}},
    )
    assert patch.status == 200

    create = await client.post(f"{PREFIX}/academy/v2/sessions/{sid}/create", json={})
    assert create.status == 201

    progress = await client.get(f"{PREFIX}/academy/v2/progress?user_id=owner")
    assert progress.status == 200


def test_docs_academy_28_6():
    assert (ROOT / "docs" / "BUILDER_ACADEMY_2.md").exists()
    assert (ROOT / "docs" / "AI_GUIDE.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "academy" / "README.md").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "academy-v2" / "AcademyV2Studio.tsx").exists()
    docs = (ROOT / "docs" / "BUILDER_ACADEMY_2.md").read_text()
    for key in ("Experience levels", "AI Guide", "Smart recommendations", "Progress tracking"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.18.0"' in manifest
    assert "29.11" in manifest
