"""Tests — Enterprise Design System (Sprint 26.2 / v9.0.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_enterprise_design_system.models import (
    ARCHITECTURE,
    CATALOG_COMPONENTS,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PRINCIPLES,
    TOKEN_GROUPS,
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
]
EDS = "/api/enterprise-eds/v1"


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


def test_version_eds_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.1.0-rc1"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.7.0"
    assert health["design_system_ready"] is True
    assert health["design_tokens_ready"] is True
    assert health["component_catalog_ready"] is True
    assert health["adaptive_grid_ready"] is True
    assert health["accessibility_ready"] is True
    assert health["design_themes_ready"] is True
    assert health["design_documentation_ready"] is True
    assert health["web_foundation_ready"] is True
    assert health["engines"]["design_system"] == "1.0"
    assert health["enterprise_certified"] is True
    assert "colors" in TOKEN_GROUPS
    assert "buttons" in CATALOG_COMPONENTS
    assert "design_tokens" in ARCHITECTURE
    assert "web_foundation" in INTEGRATION_TARGETS
    assert KPI_TARGETS["unified_design_system"] is True
    assert "phase3_design_system" in PRINCIPLES


def test_bootstrap_inventory_docs():
    suite = enterprise_hub.design_system
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["hub_version"] == "9.1.0-rc1"
    assert boot["version"] == "9.1.0-rc1"
    assert boot["design_system_ready"] is True
    assert boot["tokens_ready"] is True
    assert boot["component_catalog_ready"] is True
    assert boot["adaptive_grid_ready"] is True
    assert boot["accessibility_ready"] is True
    assert boot["themes_ready"] is True
    assert boot["documentation_ready"] is True
    assert boot["path"] == "src/web/design-system"
    assert boot["design_system_path_exists"] is True
    assert boot["tokens_css_exists"] is True
    assert boot["catalog_module_exists"] is True
    assert boot["duplicates_ui_standards"] is False
    assert boot["web_modules_use_single_ds"] is True

    inv = suite.inventory()
    assert inv["tokens"]["group_count"] >= 11
    assert inv["catalog"]["component_count"] >= 12
    assert "light" in inv["themes"]["themes"]
    assert inv["accessibility"]["standard"] == "WCAG AA"

    docs = suite.documentation()
    assert "component_guide" in docs
    assert docs["passed"] is True

    dash = suite.dashboard()
    assert dash["design_system_ready"] is True
    assert dash["catalog_count"] >= 12


@pytest.mark.asyncio
async def test_api_eds(client):
    health = await client.get(f"{EDS}/health")
    body = await health.json()
    assert body["application_version"] == "9.1.0-rc1"
    assert body["design_system_ready"] is True
    assert body["documentation_ready"] is True

    boot = await client.post(f"{EDS}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["tokens_ready"] is True

    inv = await client.get(f"{EDS}/inventory")
    assert inv.status == 200

    docs = await client.get(f"{EDS}/documentation")
    assert docs.status == 200

    dash = await client.get(f"{EDS}/dashboard")
    assert dash.status == 200

    # prior EWF remains
    ewf = await client.get("/api/enterprise-ewf/v1/health")
    assert ewf.status == 200

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.1.0-rc1"


def test_docs_and_regression_26_2():
    for name in (
        "ENTERPRISE_DESIGN_SYSTEM.md",
        "EDS_TOKENS_COLORS_TYPOGRAPHY.md",
        "EDS_GRID_ICONS_ANIMATION.md",
        "EDS_A11Y_THEME_CATALOG.md",
        "ENTERPRISE_WEB_FOUNDATION.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_DESIGN_SYSTEM.md").exists()
    assert (ROOT / "platform_enterprise_design_system" / "facade.py").exists()
    assert (ROOT / "src" / "web" / "design-system" / "index.ts").exists()
    assert (ROOT / "src" / "web" / "design-system" / "styles" / "tokens.css").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "design_system" / "facade.py").exists()

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
    assert '"application_version": "9.1.0-rc1"' in manifest
    assert "26.8" in manifest
