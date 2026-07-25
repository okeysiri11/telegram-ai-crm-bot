"""Tests — Enterprise Navigation Platform (Sprint 26.5 / v9.0.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_enterprise_navigation.models import (
    ARCHITECTURE,
    COMMAND_KINDS,
    HOTKEYS,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PRINCIPLES,
    SEARCH_CATEGORIES,
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
]
ENP = "/api/enterprise-enp/v1"


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


def test_version_enp_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.0.4"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.7.0"
    assert health["navigation_platform_ready"] is True
    assert health["command_palette_ready"] is True
    assert health["global_search_ready"] is True
    assert health["menu_engine_ready"] is True
    assert health["search_index_ready"] is True
    assert health["workspace_ready"] is True
    assert health["engines"]["navigation_platform"] == "1.0"
    assert health["enterprise_certified"] is True
    assert "command_palette" in ARCHITECTURE
    assert "open_module" in COMMAND_KINDS
    assert "crm" in SEARCH_CATEGORIES
    assert "Ctrl+K" in HOTKEYS
    assert "enterprise_hub" in INTEGRATION_TARGETS
    assert KPI_TARGETS["command_palette_ready"] is True
    assert "phase3_navigation_platform" in PRINCIPLES


def test_bootstrap_inventory_dashboard():
    suite = enterprise_hub.navigation_platform
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["hub_version"] == "9.0.4"
    assert boot["version"] == "9.0.4"
    assert boot["navigation_ready"] is True
    assert boot["command_palette_ready"] is True
    assert boot["global_search_ready"] is True
    assert boot["menu_engine_ready"] is True
    assert boot["search_index_ready"] is True
    assert boot["path"] == "src/web/navigation"
    assert boot["navigation_path_exists"] is True
    assert boot["command_palette_exists"] is True
    assert boot["search_provider_exists"] is True
    assert boot["dashboard_page_exists"] is True

    inv = suite.inventory()
    assert inv["architecture_count"] >= 12
    assert inv["search_category_count"] >= 14
    assert "fuzzy" in inv["search_modes"]
    assert "lazy_loading" in inv["performance"]

    dash = suite.dashboard()
    assert dash["command_palette_ready"] is True
    assert "Cmd+K" in dash["hotkeys"]


@pytest.mark.asyncio
async def test_api_enp(client):
    health = await client.get(f"{ENP}/health")
    body = await health.json()
    assert body["application_version"] == "9.0.4"
    assert body["navigation_ready"] is True
    assert body["command_palette_ready"] is True

    boot = await client.post(f"{ENP}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["global_search_ready"] is True

    inv = await client.get(f"{ENP}/inventory")
    assert inv.status == 200

    dash = await client.get(f"{ENP}/dashboard")
    assert dash.status == 200

    ews = await client.get("/api/enterprise-ews/v1/health")
    assert ews.status == 200

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.0.4"


def test_docs_and_regression_26_5():
    for name in (
        "ENTERPRISE_NAVIGATION.md",
        "ENP_COMMAND_PALETTE_SEARCH.md",
        "ENP_MENU_HISTORY_SHORTCUTS.md",
        "ENP_PERFORMANCE_DASHBOARD.md",
        "ENTERPRISE_WORKSPACE.md",
        "ENTERPRISE_IDENTITY_CENTER.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_NAVIGATION.md").exists()
    assert (ROOT / "platform_enterprise_navigation" / "facade.py").exists()
    assert (ROOT / "src" / "web" / "navigation" / "index.ts").exists()
    assert (ROOT / "src" / "web" / "navigation" / "components" / "CommandPalette.tsx").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "navigation_platform" / "facade.py").exists()

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
    assert '"application_version": "9.0.4"' in manifest
    assert "26.5" in manifest
