"""Tests — Enterprise Navigation Federation (Sprint 26.7 / v9.0.6)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_enterprise_navigation.models import (
    ARCHITECTURE,
    FAVORITE_KINDS,
    GLOBAL_NAV_SECTIONS,
    HISTORY_KINDS,
    HOTKEYS,
    KPI_TARGETS,
    PRINCIPLES,
    QUICK_SWITCH_TARGETS,
    SEARCH_CATEGORIES,
    SECURITY_GATES,
    WORKSPACE_KINDS,
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
]
ENV = "/api/enterprise-navigation/v1"


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


def test_version_navigation_federation_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.0.6"
    assert health["enterprise_navigation_ready"] is True
    assert health["workspace_federation_ready"] is True
    assert health["application_registry_ready"] is True
    assert health["global_search_ready"] is True
    assert health["smart_favorites_ready"] is True
    assert health["quick_switcher_ready"] is True
    assert health["navigation_analytics_ready"] is True
    assert health["engines"]["enterprise_navigation"] == "1.0"
    assert "workspace_federation" in ARCHITECTURE
    assert "crm" in GLOBAL_NAV_SECTIONS
    assert "personal" in WORKSPACE_KINDS
    assert "applications" in SEARCH_CATEGORIES
    assert "customer" in FAVORITE_KINDS
    assert "ai_chat" in HISTORY_KINDS
    assert "Ctrl+Tab" in HOTKEYS
    assert "applications" in QUICK_SWITCH_TARGETS
    assert "rbac" in SECURITY_GATES
    assert KPI_TARGETS["workspace_federation_ready"] is True
    assert "phase3_navigation_federation" in PRINCIPLES


def test_navigation_search_federation_favorites_history_analytics():
    suite = enterprise_hub.enterprise_navigation
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["hub_version"] == "9.0.6"
    assert boot["version"] == "9.0.6"
    assert boot["workspace_federation_ready"] is True
    assert boot["application_registry_ready"] is True
    assert boot["quick_switcher_ready"] is True
    assert boot["path"] == "src/web/navigation"
    assert boot["api_prefix"] == ENV
    assert boot["navigation_path_exists"] is True
    assert boot["quick_switcher_exists"] is True
    assert boot["federation_exists"] is True
    assert boot["registry_exists"] is True

    nav = suite.global_navigation()
    assert nav["count"] >= 15
    assert any(i["section"] == "crm" for i in nav["items"])

    ws = suite.workspaces()
    assert len(ws["workspaces"]) == 7
    switched = suite.switch_workspace("organization", permissions=["*"])
    assert switched["ok"] is True
    assert switched["workspace"]["kind"] == "organization"
    denied = suite.switch_workspace("ai", permissions=[])
    assert denied["ok"] is False

    registry = suite.application_registry()
    assert registry["count"] >= 10
    assert registry["auto_registered"] is True
    assert all(
        k in registry["applications"][0]
        for k in ("icon", "name", "status", "owner", "permissions", "version", "health", "last_update")
    )

    t0 = time.perf_counter()
    search = suite.search("crm")
    assert (time.perf_counter() - t0) * 1000 < 250
    assert search["fuzzy"] is True
    assert search["total"] >= 1

    fav = suite.favorites()
    assert fav["count"] >= 5
    suite.add_favorite({"id": "fav_test", "kind": "page", "label": "Test", "path": "/workspace"})
    assert suite.favorites()["count"] >= fav["count"]

    hist = suite.history()
    assert "grouped" in hist
    crumbs = suite.breadcrumbs("/workspace/crm/leads")
    assert crumbs["depth"] >= 3

    qs = suite.quick_switcher(target="workspaces")
    assert qs["ok"] is True
    assert qs["hotkey"] == "Ctrl+Tab"

    analytics = suite.analytics()
    assert analytics["dashboard_ready"] is True
    assert "popular_pages" in analytics

    perm = suite.validate_permissions("crm", ["*"])
    assert perm["allowed"] is True
    assert suite.validate_permissions("crm", [])["allowed"] is False

    inv = suite.inventory()
    assert inv["workspace_kind_count"] == 7
    assert inv["application_count"] >= 10

    dash = suite.dashboard()
    assert dash["quick_switcher_ready"] is True


@pytest.mark.asyncio
async def test_api_enterprise_navigation(client):
    health = await client.get(f"{ENV}/health")
    body = await health.json()
    assert body["application_version"] == "9.0.6"
    assert body["workspace_federation_ready"] is True

    boot = await client.post(f"{ENV}/bootstrap", json={})
    assert boot.status == 201

    for path in (
        "/inventory",
        "/dashboard",
        "/global",
        "/workspaces",
        "/registry",
        "/favorites",
        "/history",
        "/analytics",
    ):
        resp = await client.get(f"{ENV}{path}")
        assert resp.status == 200

    search = await client.post(f"{ENV}/search", json={"query": "marketplace"})
    assert search.status == 200
    assert (await search.json())["fuzzy"] is True

    switch = await client.post(
        f"{ENV}/workspaces/switch",
        json={"workspace": "project", "permissions": ["*"]},
    )
    assert switch.status == 200
    assert (await switch.json())["ok"] is True

    qs = await client.post(f"{ENV}/quick-switch", json={"target": "applications"})
    assert qs.status == 200

    crumbs = await client.get(f"{ENV}/breadcrumbs?path=/workspace/erp")
    assert crumbs.status == 200

    # prior platforms healthy
    for prefix in ("/api/enterprise-enp/v1", "/api/enterprise-command/v1", "/api/enterprise-ews/v1"):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.0.6"


def test_docs_and_regression_26_7():
    assert (ROOT / "docs" / "ENTERPRISE_NAVIGATION.md").exists()
    assert (ROOT / "knowledge" / "applications" / "enterprise_hub" / "navigation" / "README.md").exists()
    assert (ROOT / "platform_enterprise_navigation" / "facade.py").exists()
    assert (ROOT / "src" / "web" / "navigation" / "index.ts").exists()
    assert (ROOT / "src" / "web" / "navigation" / "components" / "QuickSwitcher.tsx").exists()
    assert (ROOT / "src" / "web" / "navigation" / "managers" / "workspaceFederation.ts").exists()
    assert (ROOT / "src" / "web" / "navigation" / "managers" / "applicationRegistry.ts").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "navigation" / "facade.py").exists()

    docs = (ROOT / "docs" / "ENTERPRISE_NAVIGATION.md").read_text()
    for key in ("Workspace Federation", "Ctrl+Tab", "Application Registry", "RBAC"):
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
