"""Tests — Enterprise Web Completion & Production Readiness (Sprint 32.0)."""

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
EPD = "/api/enterprise-epd/v1"
EPR = "/api/enterprise-epr/v1"
MC = "/api/platform-builder/v1/mission-control"

DOCS = [
    "PRODUCTION_STATUS_32_0.md",
    "PRODUCTION_STATUS_31_4.md",
    "ENTERPRISE_WEB_COMPLETION_32_0.md",
    "ENTERPRISE_OPERATIONS_GUIDE_32_0.md",
    "ADMINISTRATOR_GUIDE_32_0.md",
    "DEPLOYMENT_GUIDE_32_0.md",
    "PRODUCTION_CHECKLIST_32_0.md",
    "PILOT_HANDBOOK_32_0.md",
    "ARCHITECTURE_INVENTORY_32_0.md",
    "SPRINT_REPORT_32_0.md",
    "RELEASE_NOTES_32_0.md",
]

WORKSPACES = [
    "AutomotiveLiveWorkflowPage.tsx",
    "BeautyLiveWorkflowPage.tsx",
    "CafeLiveWorkflowPage.tsx",
    "AgricultureLiveWorkflowPage.tsx",
    "LegalLiveWorkflowPage.tsx",
    "BidexLiveWorkflowPage.tsx",
    "DroneLiveWorkflowPage.tsx",
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


def test_32_0_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.0" in path.read_text() or name.startswith("PRODUCTION_STATUS_31_4")


def test_platform_version_32_0():
    health = platform_builder.health()
    assert health["application_version"] == "1.64.0"
    assert health["sprint"] == "33.8"
    assert "OKR Intelligence" in health["release_status"]


def test_seven_live_workflow_pages_exist():
    web_root = ROOT / "src" / "web" / "workspace"
    found = []
    for path in web_root.rglob("*LiveWorkflowPage.tsx"):
        found.append(path.name)
    for name in WORKSPACES:
        assert name in found, name
    assert len([n for n in found if n in WORKSPACES]) == 7


def test_app_routes_and_production_page():
    app_tsx = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    for route in (
        '/workspace/auto',
        '/workspace/beauty',
        '/workspace/cafe',
        '/workspace/agro',
        '/workspace/legal',
        '/workspace/crypto',
        '/workspace/drone',
        '/pilot/production',
    ):
        assert f'path="{route}"' in app_tsx
    assert "ProductionReadinessPage" in app_tsx
    hub = (ROOT / "src" / "web" / "src" / "integrations" / "hub.ts").read_text()
    assert 'productionReadiness: "/api/enterprise-epd/v1"' in hub


def test_web_completion_audit_module():
    audit = (ROOT / "src" / "web" / "src" / "pilot" / "webCompletionAudit.ts").read_text()
    assert "WORKSPACE_HEALTH_PROBES" in audit
    assert "/workspace/drone" in audit
    assert "productionReadinessScore" in audit
    page = (ROOT / "src" / "web" / "src" / "pages" / "ProductionReadinessPage.tsx").read_text()
    assert "Production Readiness" in page
    assert "hubIntegrations.productionReadiness" in page


@pytest.mark.asyncio
async def test_epd_and_mc_probes(client):
    epd = await client.get(f"{EPD}/health")
    assert epd.status == 200
    body = await epd.json()
    assert body.get("status") == "ok"

    dash = await client.get(f"{EPD}/dashboard")
    assert dash.status == 200

    epr = await client.get(f"{EPR}/health")
    assert epr.status == 200

    mc = await client.get(f"{MC}/status")
    assert mc.status == 200


def test_config_and_manifest_32_0():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.64.0"' in cfg
    assert 'sprint: str = "33.8"' in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.64.0"' in manifest
    assert '"sprint": "33.8"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.8"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.64.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.8"' in types


def test_architecture_index_lists_32_0():
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "32.0" in index
    assert "ENTERPRISE_WEB_COMPLETION_32_0.md" in index
