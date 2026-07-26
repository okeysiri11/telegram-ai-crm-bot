"""Tests — First External Pilot Execution & Product Feedback Loop (Sprint 32.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.platform_builder.api.register import register_platform_builder_routes


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "PILOT_OPS_32_2.md",
    "EXTERNAL_ONBOARDING_GUIDE_32_2.md",
    "RELEASE_NOTES_32_2.md",
    "KNOWN_ISSUES_32_2.md",
    "METRICS_DASHBOARD_32_2.md",
    "ENTERPRISE_READINESS_REPORT_32_2.md",
    "PRODUCTION_STATUS_32_2.md",
    "ROLLBACK_CHECKLIST_32_2.md",
    "RISK_ASSESSMENT_32_2.md",
    "SPRINT_REPORT_32_2.md",
]


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_enterprise_hub_routes(application)
    register_platform_builder_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    enterprise_hub.reset()
    yield
    platform_builder.reset()
    enterprise_hub.reset()


def test_32_2_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.2" in path.read_text()


def test_platform_version_32_2():
    health = platform_builder.health()
    assert health["application_version"] == "1.65.0"
    assert health["sprint"] == "33.9"
    assert "Governance" in health["release_status"]


def test_pilot_execution_page_and_route():
    app_tsx = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/pilot/execute"' in app_tsx
    assert "PilotExecutionPage" in app_tsx
    page = (ROOT / "src" / "web" / "src" / "pages" / "PilotExecutionPage.tsx").read_text()
    for phase in ("build", "validate", "pilot", "measure", "improve", "release"):
        assert phase in page.lower() or phase.capitalize() in page
    assert "pilotMetrics.snapshot" in page
    assert "FEEDBACK_MODULE_CHECKLIST" in page
    metrics = (ROOT / "src" / "web" / "src" / "integrations" / "pilotMetrics.ts").read_text()
    assert "recordOnboarding" in metrics
    assert "recordInvitation" in metrics
    assert "registrations" in metrics
    feedback = (ROOT / "src" / "web" / "src" / "integrations" / "pilotFeedback.ts").read_text()
    assert "FEEDBACK_MODULE_CHECKLIST" in feedback
    assert "feedbackBacklogSummary" in feedback
    mc = (
        ROOT / "src" / "web" / "platform-builder" / "mission-control" / "MissionControlLivePanel.tsx"
    ).read_text()
    assert "Pilot KPIs" in mc
    assert "Pilot organizations" in mc
    assert "/pilot/execute" in mc


@pytest.mark.asyncio
async def test_tenancy_and_epd_for_release_phase(client):
    tn = await client.get("/api/enterprise-tenancy/v1/health")
    assert tn.status == 200
    epd = await client.get("/api/enterprise-epd/v1/health")
    assert epd.status == 200
    epr = await client.get("/api/enterprise-epr/v1/health")
    assert epr.status == 200


def test_config_manifest_32_2():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.65.0"' in cfg
    assert 'sprint: str = "33.9"' in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.65.0"' in manifest
    assert '"sprint": "33.9"' in manifest


def test_architecture_index_lists_32_2():
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "32.2" in index
    assert "PILOT_OPS_32_2.md" in index
