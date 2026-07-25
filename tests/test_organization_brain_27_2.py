"""Tests — Enterprise Organization Brain (Sprint 27.2 / v9.4.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_organization_brain.models import (
    ARCHITECTURE,
    DEPARTMENTS,
    EXECUTIVE_BOARD,
    KPI_TARGETS,
    KNOWLEDGE_KINDS,
    ORG_ENTITY_TYPES,
    PRINCIPLES,
    VERSION,
)


ROOT = Path(__file__).resolve().parents[1]
PREFIXES = [
    "/api/enterprise-hub/v1",
    "/api/enterprise-orch/v1",
    "/api/enterprise-kg/v1",
    "/api/enterprise-agents/v1",
    "/api/enterprise-comms/v1",
    "/api/enterprise-workflow/v1",
    "/api/enterprise-eip/v1",
    "/api/enterprise-edp/v1",
    "/api/enterprise-isam/v1",
    "/api/enterprise-obs/v1",
    "/api/enterprise-tenancy/v1",
    "/api/enterprise-aop/v1",
    "/api/enterprise-ats/v1",
    "/api/enterprise-ekp/v1",
    "/api/enterprise-aios/v1",
    "/api/enterprise-evp/v1",
    "/api/enterprise-sdp/v1",
    "/api/enterprise-edf/v1",
    "/api/enterprise-edt/v1",
    "/api/enterprise-esi/v1",
    "/api/enterprise-epm/v1",
    "/api/enterprise-ebc/v1",
    "/api/enterprise-ecc/v1",
    "/api/enterprise-eas/v1",
    "/api/enterprise-edc/v1",
    "/api/enterprise-esh/v1",
    "/api/enterprise-eqa/v1",
    "/api/enterprise-edo/v1",
    "/api/enterprise-epf/v1",
    "/api/enterprise-erl/v1",
    "/api/enterprise-epi/v1",
    "/api/enterprise-aba/v1",
    "/api/enterprise-bos/v1",
    "/api/enterprise-bws/v1",
    "/api/enterprise-bcj/v1",
    "/api/enterprise-amo/v1",
    "/api/enterprise-ech/v1",
    "/api/enterprise-eco/v1",
    "/api/enterprise-cpl/v1",
    "/api/enterprise-eon/v1",
    "/api/enterprise-eoc/v1",
    "/api/enterprise-epr/v1",
    "/api/enterprise-eao/v1",
    "/api/enterprise-wfi/v1",
    "/api/enterprise-ekg/v1",
    "/api/enterprise-pin/v1",
    "/api/enterprise-esl/v1",
    "/api/enterprise-etw/v1",
    "/api/enterprise-eoe/v1",
    "/api/enterprise-est/v1",
    "/api/enterprise-ele/v1",
    "/api/enterprise-aph/v1",
    "/api/enterprise-ees/v1",
    "/api/enterprise-eti/v1",
    "/api/enterprise-epl/v1",
    "/api/enterprise-ece/v1",
    "/api/enterprise-emr/v1",
    "/api/enterprise-esv/v1",
    "/api/enterprise-epd/v1",
    "/api/enterprise-ecf/v1",
    "/api/enterprise-ewf/v1",
    "/api/enterprise-eds/v1",
    "/api/enterprise-eic/v1",
    "/api/enterprise-ews/v1",
    "/api/enterprise-enp/v1",
    "/api/enterprise-command/v1",
    "/api/enterprise-navigation/v1",
    "/api/release/v1",
    "/api/ai-os/v1/maos",
]
OBR = "/api/organization-brain/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_enterprise_hub_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    enterprise_hub.reset()
    yield
    enterprise_hub.reset()


def test_version_organization_brain_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.4.0"
    assert health["organization_brain_ready"] is True
    assert health["executive_board_ready"] is True
    assert health["department_orchestration_ready"] is True
    assert health["decision_engine_ready"] is True
    assert health["executive_meetings_ready"] is True
    assert health["organization_knowledge_ready"] is True
    assert health["org_executive_dashboard_ready"] is True
    assert health["engines"]["organization_brain"] == "1.0"
    assert VERSION == "9.4.0"
    assert "organization_model" in ARCHITECTURE
    assert "CEO" in EXECUTIVE_BOARD
    assert "Sales" in DEPARTMENTS
    assert "companies" in ORG_ENTITY_TYPES
    assert "policies" in KNOWLEDGE_KINDS
    assert KPI_TARGETS["decision_engine_ready"] is True
    assert "phase4_organization_brain" in PRINCIPLES


def test_org_board_departments_decisions_meetings_knowledge():
    suite = enterprise_hub.organization_brain
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["hub_version"] == "9.4.0"
    assert boot["organization_model_ready"] is True
    assert boot["executive_board_ready"] is True
    assert boot["decision_engine_ready"] is True
    assert boot["organization_brain_path_exists"] is True
    assert boot["dashboard_page_exists"] is True
    assert boot["hub_suite_exists"] is True

    org = suite.organization()
    assert org["ready"] is True
    assert org["hierarchy"]["depth"] >= 3
    assert len(org["companies"]) >= 1
    assert len(org["holdings"]) >= 1
    assert len(org["employees"]) >= 1
    assert len(org["roles"]) >= 1
    assert len(org["positions"]) >= 1

    board = suite.board()
    assert board["count"] == 7
    titles = {m["title"] for m in board["members"]}
    assert titles == set(EXECUTIVE_BOARD)

    depts = suite.departments()
    assert depts["count"] == len(DEPARTMENTS)
    orch = suite.orchestrate_department(department="Sales", objective="Close Q3 pipeline")
    assert orch["ok"] is True
    assert orch["department"] == "Sales"
    assert len(orch["tasks"]) >= 2

    decision = suite.decide(topic="Invest in logistics capacity")
    assert decision["ok"] is True
    assert decision["risks"]
    assert decision["chosen"]
    assert decision["tasks"]
    assert decision["resources"]["budget_usd"] > 0
    assert "ARR" in decision["kpi_controls"]

    meeting = suite.meeting(topic="Approve AI hiring plan")
    assert meeting["ok"] is True
    assert meeting["protocol"]["agreement"] is True
    assert meeting["decision"]
    assert len(meeting["owners"]) >= 2
    assert suite.meetings()["count"] >= 1

    kg = suite.knowledge_write(kind="policies", content="New AI spend policy")
    assert kg["ok"] is True
    snap = suite.knowledge()
    assert snap["counts"]["policies"] >= 1
    assert "structure" in snap["kinds"]

    dash = suite.dashboard()
    assert dash["title"] == "Organization Executive Dashboard"
    assert "kpi" in dash
    assert "department_efficiency" in dash
    assert "financials" in dash
    assert "strategic_goals" in dash
    assert "alerts" in dash
    assert "recommendations" in dash


@pytest.mark.asyncio
async def test_api_organization_brain(client):
    health = await client.get(f"{OBR}/health")
    body = await health.json()
    assert body["application_version"] == "9.4.0"
    assert body["organization_brain_ready"] is True

    boot = await client.post(f"{OBR}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["executive_board_ready"] is True

    inv = await client.get(f"{OBR}/inventory")
    assert inv.status == 200

    org = await client.get(f"{OBR}/organization")
    assert org.status == 200
    assert (await org.json())["ready"] is True

    board = await client.get(f"{OBR}/board")
    assert board.status == 200
    assert (await board.json())["count"] == 7

    depts = await client.get(f"{OBR}/departments")
    assert depts.status == 200

    orch = await client.post(
        f"{OBR}/departments/orchestrate",
        json={"department": "Finance", "objective": "Close month"},
    )
    assert orch.status == 200
    assert (await orch.json())["ok"] is True

    dec = await client.post(f"{OBR}/decisions", json={"topic": "Expand CRM automation"})
    assert dec.status == 200

    mtg = await client.post(f"{OBR}/meetings", json={"topic": "Budget reallocation"})
    assert mtg.status == 200

    kg = await client.post(
        f"{OBR}/knowledge",
        json={"kind": "kpi", "content": "Target AI utilization 70%"},
    )
    assert kg.status == 200

    dash = await client.get(f"{OBR}/exec-dashboard")
    assert dash.status == 200

    for prefix in (
        "/api/ai-os/v1/maos",
        "/api/release/v1",
        "/api/enterprise-navigation/v1",
        "/api/enterprise-command/v1",
    ):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "9.4.0"

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        data = await resp.json()
        version = data.get("application_version") or data.get("data", {}).get("application_version")
        assert version == "9.4.0"


def test_docs_and_regression_27_2():
    assert (ROOT / "docs" / "ENTERPRISE_ORGANIZATION_BRAIN.md").exists()
    assert (ROOT / "platform_organization_brain" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "organization_brain" / "facade.py").exists()
    assert (ROOT / "src" / "web" / "organization-brain" / "pages" / "OrganizationBrainPage.tsx").exists()
    assert (ROOT / "knowledge" / "applications" / "enterprise_hub" / "organization_brain" / "README.md").exists()

    docs = (ROOT / "docs" / "ENTERPRISE_ORGANIZATION_BRAIN.md").read_text()
    for key in ("Organization Model", "Executive Board", "Decision Engine", "Executive Meetings"):
        assert key in docs

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS_CFG
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO

    assert AIOS_CFG.api_prefix == "/api/ai-os/v1"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert '"application_version": "9.4.0"' in manifest
    assert "27.3" in manifest
