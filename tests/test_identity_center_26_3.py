"""Tests — Enterprise Identity Center (Sprint 26.3 / v9.0.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_enterprise_identity_center.models import (
    ARCHITECTURE,
    AUTH_PAGES,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    MFA_METHODS,
    PRINCIPLES,
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
]
EIC = "/api/enterprise-eic/v1"


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


def test_version_eic_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.2.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.7.0"
    assert health["authentication_ui_ready"] is True
    assert health["identity_center_ready"] is True
    assert health["identity_mfa_ready"] is True
    assert health["session_management_ready"] is True
    assert health["identity_security_center_ready"] is True
    assert health["identity_profile_center_ready"] is True
    assert health["design_system_ready"] is True
    assert health["web_foundation_ready"] is True
    assert health["engines"]["identity_center"] == "1.0"
    assert health["enterprise_certified"] is True
    assert "login" in AUTH_PAGES
    assert "authentication_ui" in ARCHITECTURE
    assert "totp" in MFA_METHODS
    assert "enterprise_hub" in INTEGRATION_TARGETS
    assert KPI_TARGETS["authentication_ui_ready"] is True
    assert "phase3_identity_center" in PRINCIPLES


def test_bootstrap_inventory_dashboard():
    suite = enterprise_hub.identity_center
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["hub_version"] == "9.2.0"
    assert boot["version"] == "9.2.0"
    assert boot["authentication_ui_ready"] is True
    assert boot["identity_center_ready"] is True
    assert boot["mfa_ready"] is True
    assert boot["session_management_ready"] is True
    assert boot["security_center_ready"] is True
    assert boot["profile_center_ready"] is True
    assert boot["enterprise_core_integrated"] is True
    assert boot["path"] == "src/web/auth"
    assert boot["auth_path_exists"] is True
    assert boot["login_page_exists"] is True
    assert boot["identity_dashboard_exists"] is True
    assert boot["mfa_center_exists"] is True

    inv = suite.inventory()
    assert inv["page_count"] >= 8
    assert inv["architecture_count"] >= 12
    assert "crm" in inv["permission_domains"]
    assert "fido2" in inv["mfa_extensions"]

    dash = suite.dashboard()
    assert dash["authentication_ui_ready"] is True
    assert dash["rbac_synced"] is True


@pytest.mark.asyncio
async def test_api_eic(client):
    health = await client.get(f"{EIC}/health")
    body = await health.json()
    assert body["application_version"] == "9.2.0"
    assert body["identity_center_ready"] is True
    assert body["mfa_ready"] is True

    boot = await client.post(f"{EIC}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["authentication_ui_ready"] is True

    inv = await client.get(f"{EIC}/inventory")
    assert inv.status == 200

    dash = await client.get(f"{EIC}/dashboard")
    assert dash.status == 200

    eds = await client.get("/api/enterprise-eds/v1/health")
    assert eds.status == 200

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.2.0"


def test_docs_and_regression_26_3():
    for name in (
        "ENTERPRISE_IDENTITY_CENTER.md",
        "EIC_AUTH_UI_MFA.md",
        "EIC_IDENTITY_RBAC.md",
        "EIC_SECURITY_PROFILE.md",
        "ENTERPRISE_DESIGN_SYSTEM.md",
        "ENTERPRISE_WEB_FOUNDATION.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_IDENTITY_CENTER.md").exists()
    assert (ROOT / "platform_enterprise_identity_center" / "facade.py").exists()
    assert (ROOT / "src" / "web" / "auth" / "index.ts").exists()
    assert (ROOT / "src" / "web" / "auth" / "pages" / "LoginPage.tsx").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "identity_center" / "facade.py").exists()

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
    assert '"application_version": "9.2.0"' in manifest
    assert "27.1" in manifest
