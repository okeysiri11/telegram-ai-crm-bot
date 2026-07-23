"""Tests — Case Management Platform (Sprint 17.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from applications.legal_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/legal-enterprise/v1"
LI = "/api/legal-li/v1"
JI = "/api/legal-ji/v1"
CM = "/api/legal-cm/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_legal_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    legal_enterprise.reset()
    yield
    legal_enterprise.reset()


def test_version_case_management_ready():
    health = legal_enterprise.health()
    assert health["application_version"] == "4.9.5-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.9.4-enterprise"
    assert health["case_management_ready"] is True
    assert health["court_calendar_ready"] is True
    assert health["procedural_timeline_ready"] is True
    assert health["ai_legal_workflow_ready"] is True
    assert health["judicial_intelligence_ready"] is True


def test_cases_calendar_and_deadlines():
    suite = legal_enterprise.case_management_platform
    case = suite.cases.register(title="QA Matter", category="civil", priority="high")
    room = suite.calendar.register_courtroom(name="Room 1")
    hearing = suite.calendar.schedule_hearing(
        case_id=case["case_id"],
        title="Hearing",
        scheduled_at="2026-08-01T10:00:00Z",
        courtroom_id=room["courtroom_id"],
    )
    assert hearing["hearing_id"]
    dl = suite.deadlines.register_deadline(
        case_id=case["case_id"], deadline_type="filing", due_on="2026-07-30", risk="high"
    )
    assert dl["deadline_id"]
    with pytest.raises(ValidationError):
        suite.cases.register(title="", category="civil")


def test_workflow_ai_and_bootstrap():
    suite = legal_enterprise.case_management_platform
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.9.5-enterprise"
    assert boot["case_id"] and boot["hearing_id"] and boot["health_id"]
    assert suite.ai.health_score(case_id=boot["case_id"])["kind"] == "health_score"
    assert suite.tasks.status()["tasks"] >= 1
    assert suite.documents.status()["documents"] >= 3
    for dtype in ("case", "calendar", "deadline", "workflow", "ai_case"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_case_management(client):
    health = await client.get(f"{CM}/health")
    body = await health.json()
    assert body["application_version"] == "4.9.5-enterprise"
    assert body["case_management_ready"] is True
    assert body["court_calendar_ready"] is True

    boot = await client.post(f"{CM}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    dl = await client.post(
        f"{CM}/deadlines",
        json={
            "action": "calculate",
            "case_id": boot_body["case_id"],
            "deadline_type": "procedural",
            "from_date": "2026-07-21T00:00:00Z",
            "days": 7,
        },
    )
    assert dl.status == 201

    ai = await client.post(
        f"{CM}/ai",
        json={"action": "summary", "case_id": boot_body["case_id"]},
    )
    assert ai.status == 201

    for prefix in (PREFIX, LI, JI):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "4.9.5-enterprise"


def test_docs_and_regression_17_3():
    for name in (
        "CASE_MANAGEMENT_PLATFORM.md",
        "COURT_CALENDAR.md",
        "PROCEDURAL_TIMELINE.md",
        "LEGAL_WORKFLOW.md",
        "AI_CASE_MANAGEMENT.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CASE_MANAGEMENT_PLATFORM.md").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "case_management" / "facade.py").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "cases.py").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "judicial_intelligence" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    manifest = (ROOT / "applications" / "legal_enterprise" / "manifest.json").read_text()
    assert "4.9.5-enterprise" in manifest
    assert "17.5" in manifest
