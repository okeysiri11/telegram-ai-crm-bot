"""Tests — Enterprise Developer Platform (Sprint 20.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
HUB = "/api/enterprise-hub/v1"
ORCH = "/api/enterprise-orch/v1"
KG = "/api/enterprise-kg/v1"
AA = "/api/enterprise-agents/v1"
CM = "/api/enterprise-comms/v1"
WF = "/api/enterprise-workflow/v1"
EIP = "/api/enterprise-eip/v1"
EDP = "/api/enterprise-edp/v1"
ISAM = "/api/enterprise-isam/v1"
OBS = "/api/enterprise-obs/v1"
TN = "/api/enterprise-tenancy/v1"
AOP = "/api/enterprise-aop/v1"
ATS = "/api/enterprise-ats/v1"
EKP = "/api/enterprise-ekp/v1"
AIOS = "/api/enterprise-aios/v1"
EVP = "/api/enterprise-evp/v1"
SDP = "/api/enterprise-sdp/v1"


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


def test_version_sdp_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.1.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.0.0"
    assert health["developer_platform_ready"] is True
    assert health["plugin_framework_ready"] is True
    assert health["sdk_ready"] is True
    assert health["marketplace_ready"] is True
    assert health["event_platform_ready"] is True
    assert health["engines"]["developer_platform"] == "1.0"
    assert health["engines"]["event_platform"] == "1.0"


def test_plugin_lifecycle_sandbox_sdk():
    suite = enterprise_hub.developer_platform
    installed = suite.plugins.install_from_manifest(
        plugin_id="demo-plugin",
        name="Demo Plugin",
        version="1.0.0",
        permissions=["crm.read", "ui.extend"],
    )
    assert installed["status"] == "active"
    hot = suite.lifecycle.hot_reload(plugin_id="demo-plugin")
    assert hot["zero_downtime"] is True
    rb = suite.lifecycle.rollback(plugin_id="demo-plugin", to_version="0.9.0")
    assert rb["to_version"] == "0.9.0"
    suite.lifecycle.activate(plugin_id="demo-plugin")
    sbx = suite.sandbox.create(plugin_id="demo-plugin", allow_network=False)
    check = suite.sandbox.check(sandbox_id=sbx["sandbox_id"], needs_network=True)
    assert check["allowed"] is False
    call = suite.sdk.call(surface="crm", method="get_lead", plugin_id="demo-plugin")
    assert call["result"]["ok"] is True
    with pytest.raises(ValidationError):
        suite.plugins.install_from_manifest(plugin_id="", name="x")


def test_bootstrap_marketplace_console():
    suite = enterprise_hub.developer_platform
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.1.0"
    assert boot["dependency_compatible"] is True
    assert boot["sandbox_network_denied"] is True
    assert boot["updates_available"] is True
    assert boot["hot_reload_id"] and boot["rollback_id"]
    assert boot["console_plugins"] >= 2
    assert boot["sdk_docs_surfaces"] >= 8
    console = suite.console()
    assert console["plugin_count"] >= 2
    assert console["sdk_docs"]["version"] == "1.0"


@pytest.mark.asyncio
async def test_api_sdp(client):
    health = await client.get(f"{SDP}/health")
    body = await health.json()
    assert body["application_version"] == "7.1.0"
    assert body["developer_platform_ready"] is True

    boot = await client.post(f"{SDP}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{SDP}/plugins",
        json={
            "plugin_id": "api-plugin",
            "name": "API Plugin",
            "permissions": ["events.publish"],
        },
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP, AIOS, EVP):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "7.1.0"

    assert boot_body["publish_id"]


def test_docs_and_regression_20_6():
    for name in (
        "ENTERPRISE_DEVELOPER_PLATFORM.md",
        "SDP_PLUGIN_FRAMEWORK.md",
        "SDP_SDK.md",
        "SDP_MARKETPLACE.md",
        "SDP_SANDBOX_PACKAGES.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_DEVELOPER_PLATFORM.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "developer_platform" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "developer_platform" / "sdk" / "crm_sdk.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "developer_platform" / "marketplace" / "publisher.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "developer_platform" / "templates" / "plugin_template" / "manifest.json").exists()

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
    assert "7.1.0" in manifest
    assert "24.1" in manifest
