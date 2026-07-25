"""Tests — Enterprise Command Center & Productivity Platform (Sprint 26.6 / v9.0.6)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_enterprise_command_center.models import (
    AI_COMMANDS,
    ARCHITECTURE,
    HOTKEYS,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    OMNIBOX_SOURCES,
    PRINCIPLES,
    PRODUCTIVITY_WIDGETS,
    QUICK_ACTIONS,
    SECURITY_GATES,
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
]
ECC2 = "/api/enterprise-command/v1"


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


def test_version_command_center_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.0.6"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.7.0"
    assert health["enterprise_command_center_ready"] is True
    assert health["universal_command_palette_ready"] is True
    assert health["omnibox_ready"] is True
    assert health["productivity_hub_ready"] is True
    assert health["ai_command_center_ready"] is True
    assert health["navigation_platform_ready"] is True
    assert health["workspace_ready"] is True
    assert health["engines"]["enterprise_command_center"] == "1.0"
    assert health["enterprise_certified"] is True
    assert "universal_command_palette" in ARCHITECTURE
    assert "crm" in OMNIBOX_SOURCES
    assert "create_client" in QUICK_ACTIONS
    assert "recent_activity" in PRODUCTIVITY_WIDGETS
    assert "open_crm" in AI_COMMANDS
    assert "Ctrl+K" in HOTKEYS
    assert "Ctrl+Shift+P" in HOTKEYS
    assert "rbac" in SECURITY_GATES
    assert "enterprise_hub" in INTEGRATION_TARGETS
    assert KPI_TARGETS["omnibox_ready"] is True
    assert "phase3_command_center" in PRINCIPLES


def test_search_actions_ai_permissions_analytics():
    suite = enterprise_hub.command_center_platform
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["hub_version"] == "9.0.6"
    assert boot["version"] == "9.0.6"
    assert boot["command_center_ready"] is True
    assert boot["command_palette_ready"] is True
    assert boot["omnibox_ready"] is True
    assert boot["productivity_hub_ready"] is True
    assert boot["ai_command_center_ready"] is True
    assert boot["path"] == "src/web/command-center"
    assert boot["api_prefix"] == ECC2
    assert boot["command_center_path_exists"] is True
    assert boot["palette_exists"] is True
    assert boot["omnibox_exists"] is True
    assert boot["productivity_page_exists"] is True
    assert boot["platform_package_exists"] is True
    assert boot["legacy_ecc_exists"] is True

    t0 = time.perf_counter()
    search = suite.search("crm")
    elapsed = (time.perf_counter() - t0) * 1000
    assert search["fuzzy"] is True
    assert search["total"] >= 1
    assert any(r["title"].lower().find("crm") >= 0 or r.get("type") == "modules" for r in search["results"])
    assert elapsed < 250  # performance gate

    fuzzy = suite.search("acme")
    assert any("acme" in r["title"].lower() for r in fuzzy["results"])

    exec_ok = suite.execute("open_crm", permissions=["*"])
    assert exec_ok["ok"] is True
    assert exec_ok["route"] == "/workspace/crm"
    assert exec_ok["audit"]["event"] == "command_executed"

    denied = suite.execute("open_crm", permissions=[])
    assert denied["ok"] is False
    assert denied["error"] == "permission_denied"

    ai = suite.ai_command("Open CRM please")
    assert ai["ok"] is True
    assert ai["intent"] == "open_crm"

    ai2 = suite.ai_command("Generate weekly report")
    assert ai2["ok"] is True

    sugg = suite.suggestions(limit=5)
    assert sugg["count"] == 5

    ctx = suite.context({"selected_customer": "acme"})
    assert ctx["selected_customer"] == "acme"

    prod = suite.productivity()
    assert "recent_activity" in prod["widgets"]

    analytics = suite.analytics()
    assert analytics["dashboard_ready"] is True
    assert "popular_commands" in analytics

    nav = suite.navigation_index()
    assert nav["total"] >= 15
    assert "applications" in nav["types"]

    inv = suite.inventory()
    assert inv["architecture_count"] >= 12
    assert inv["omnibox_source_count"] >= 15
    assert inv["quick_action_count"] >= 15

    dash = suite.dashboard()
    assert dash["command_analytics_ready"] is True
    assert "Cmd+K" in dash["hotkeys"] or "Ctrl+K" in dash["hotkeys"]

    perm = suite.validate_permissions("open_crm", ["*"])
    assert perm["allowed"] is True


@pytest.mark.asyncio
async def test_api_enterprise_command(client):
    health = await client.get(f"{ECC2}/health")
    body = await health.json()
    assert body["application_version"] == "9.0.6"
    assert body["command_center_ready"] is True
    assert body["omnibox_ready"] is True

    boot = await client.post(f"{ECC2}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["ai_command_center_ready"] is True

    search = await client.post(f"{ECC2}/search", json={"query": "marketplace"})
    assert search.status == 200
    assert (await search.json())["fuzzy"] is True

    exe = await client.post(f"{ECC2}/execute", json={"action": "open_settings", "permissions": ["*"]})
    assert exe.status == 200
    assert (await exe.json())["ok"] is True

    ai = await client.post(f"{ECC2}/ai", json={"utterance": "Open ERP"})
    assert ai.status == 200
    assert (await ai.json())["ok"] is True

    for path in (
        "/inventory",
        "/dashboard",
        "/suggestions",
        "/context",
        "/productivity",
        "/analytics",
        "/navigation-index",
    ):
        resp = await client.get(f"{ECC2}{path}")
        assert resp.status == 200

    perm = await client.post(f"{ECC2}/permissions", json={"action": "open_crm", "permissions": ["*"]})
    assert perm.status == 200

    # prior platforms still healthy
    enp = await client.get("/api/enterprise-enp/v1/health")
    assert enp.status == 200
    ews = await client.get("/api/enterprise-ews/v1/health")
    assert ews.status == 200
    ecc = await client.get("/api/enterprise-ecc/v1/health")
    assert ecc.status == 200

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.0.6"


def test_docs_and_regression_26_6():
    assert (ROOT / "docs" / "ENTERPRISE_COMMAND_CENTER.md").exists()
    assert (ROOT / "knowledge" / "applications" / "enterprise_hub" / "command_center" / "README.md").exists()
    assert (ROOT / "platform_enterprise_command_center" / "facade.py").exists()
    assert (ROOT / "src" / "web" / "command-center" / "index.ts").exists()
    assert (ROOT / "src" / "web" / "command-center" / "components" / "UniversalCommandPalette.tsx").exists()
    assert (ROOT / "src" / "web" / "command-center" / "components" / "Omnibox.tsx").exists()
    assert (ROOT / "src" / "web" / "command-center" / "pages" / "CommandCenterPage.tsx").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "command_center_platform" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "command_center" / "enterprise_command.py").exists()

    # keyboard shortcuts documented
    docs = (ROOT / "docs" / "ENTERPRISE_COMMAND_CENTER.md").read_text()
    for key in ("Ctrl/Cmd+K", "Ctrl+P", "Ctrl+Shift+P", "Omnibox", "RBAC"):
        assert key in docs

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS_CFG
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS_CFG.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert '"application_version": "9.0.6"' in manifest
    assert "26.7" in manifest
