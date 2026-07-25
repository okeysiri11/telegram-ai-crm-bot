"""Tests — Enterprise Web Foundation (Sprint 26.1 / v9.0.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_enterprise_web.models import INTEGRATION_TARGETS, KPI_TARGETS, PRINCIPLES, STACK, UI_COMPONENTS


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
]
EWF = "/api/enterprise-ewf/v1"


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


def test_version_ewf_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.0.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.7.0"
    assert health["web_foundation_ready"] is True
    assert health["web_shell_ready"] is True
    assert health["navigation_ready"] is True
    assert health["ui_library_ready"] is True
    assert health["web_auth_ready"] is True
    assert health["web_multi_tenant_ready"] is True
    assert health["themes_localization_ready"] is True
    assert health["web_dashboard_ready"] is True
    assert health["engines"]["web_foundation"] == "1.0"
    assert health["enterprise_certified"] is True
    assert "react_19" in STACK
    assert "button" in UI_COMPONENTS
    assert "enterprise_hub" in INTEGRATION_TARGETS
    assert KPI_TARGETS["modules_plug_in_without_arch_change"] is True
    assert "phase3_foundation" in PRINCIPLES


def test_bootstrap_and_inventory():
    suite = enterprise_hub.web_foundation
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "9.0.0"
    assert boot["web_foundation_ready"] is True
    assert boot["web_shell_ready"] is True
    assert boot["ui_library_ready"] is True
    assert boot["auth_ready"] is True
    assert boot["multi_tenant_ready"] is True
    assert boot["dashboard_ready"] is True
    assert boot["path"] == "src/web"
    assert boot["web_path_exists"] is True
    assert boot["package_json_exists"] is True
    assert boot["modules_plug_in_without_arch_change"] is True
    assert boot["duplicates_core_logic"] is False
    assert "react_19" in boot["stack"]

    inv = suite.inventory()
    assert inv["catalog"]["ui_count"] >= 20
    assert "en" in inv["catalog"]["locales"]
    assert "ru" in inv["catalog"]["locales"]
    assert "uk" in inv["catalog"]["locales"]
    assert inv["auth"]["mfa_ready"] is True

    dash = suite.dashboard()
    assert dash["web_shell_ready"] is True
    assert dash["ui_library_ready"] is True


@pytest.mark.asyncio
async def test_api_ewf(client):
    health = await client.get(f"{EWF}/health")
    body = await health.json()
    assert body["application_version"] == "9.0.0"
    assert body["web_foundation_ready"] is True
    assert body["dashboard_ready"] is True

    boot = await client.post(f"{EWF}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["ui_library_ready"] is True

    inv = await client.get(f"{EWF}/inventory")
    assert inv.status == 200

    # prior ECF remains
    ecf = await client.get("/api/enterprise-ecf/v1/health")
    assert ecf.status == 200

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.0.0"


def test_docs_and_regression_26_1():
    for name in (
        "ENTERPRISE_WEB_FOUNDATION.md",
        "EWF_SHELL_AUTH_LAYOUT.md",
        "EWF_UI_I18N_THEME.md",
        "EWF_DASHBOARD_INTEGRATION.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_WEB_FOUNDATION.md").exists()
    assert (ROOT / "platform_enterprise_web" / "facade.py").exists()
    assert (ROOT / "src" / "web" / "package.json").exists()
    assert (ROOT / "src" / "web" / "src" / "App.tsx").exists()
    assert (ROOT / "src" / "web" / "src" / "ui" / "Button.tsx").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "web_foundation" / "facade.py").exists()

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
    assert '"application_version": "9.0.0"' in manifest
    assert "26.1" in manifest
