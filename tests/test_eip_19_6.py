"""Tests — Enterprise Integration Platform (Sprint 19.6)."""

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


def test_version_eip_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.5.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.4.0"
    assert health["enterprise_integration_platform_ready"] is True
    assert health["connector_engine_ready"] is True
    assert health["adapter_layer_ready"] is True
    assert health["sync_engine_ready"] is True
    assert health["enterprise_workflow_ready"] is True
    assert health["engines"]["eip"] == "1.0"
    assert health["engines"]["integration_layer"] == "1.0"


def test_manager_engine_mapping_sync():
    suite = enterprise_hub.eip
    reg = suite.manager.register(
        name="QA REST",
        protocol="rest",
        adapter="custom",
        owner="qa",
    )
    suite.manager.start(integration_id=reg["integration_id"])
    call = suite.engine.connect(protocol="rest", endpoint="/qa")
    adp = suite.engine.adapt(adapter="gmail", operation="send")
    sync = suite.engine.sync(integration_id=reg["integration_id"], mode="full", records=3)
    mapped = suite.mapper.map_fields(
        source_fields={"a": 1},
        mapping={"a": "alpha"},
    )
    assert call["call_id"] and adp["call_id"] and sync["sync_id"]
    assert mapped["result"]["alpha"] == 1
    with pytest.raises(ValidationError):
        suite.manager.register(name="", protocol="rest")


def test_security_monitor_ai_bootstrap():
    suite = enterprise_hub.eip
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.5.0"
    assert boot["integration_stripe_id"] and boot["retry_id"] and boot["ai_mapping_id"]
    sec = suite.security.configure(
        integration_id=boot["integration_telegram_id"], method="jwt"
    )
    assert sec["method"] == "jwt"
    mon = suite.monitor.snapshot(integration_id=boot["integration_telegram_id"], latency_ms=11)
    assert mon["monitor_id"]
    for dtype in ("monitoring", "registry", "sync", "connectors", "analytics"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_eip(client):
    health = await client.get(f"{EIP}/health")
    body = await health.json()
    assert body["application_version"] == "6.5.0"
    assert body["enterprise_integration_platform_ready"] is True
    assert body["connector_engine_ready"] is True

    boot = await client.post(f"{EIP}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{EIP}/manager",
        json={"name": "API Connector", "protocol": "graphql", "adapter": "custom"},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "6.5.0"

    assert boot_body["adapter_binance_id"]


def test_docs_and_regression_19_6():
    for name in (
        "ENTERPRISE_INTEGRATION_PLATFORM.md",
        "EIP_CONNECTORS.md",
        "EIP_ADAPTERS.md",
        "EIP_MAPPING.md",
        "EIP_SYNC.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_INTEGRATION_PLATFORM.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "integrations" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "integrations" / "connectors" / "rest.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "integrations" / "adapters" / "stripe.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "integrations" / "mapping" / "field_mapper.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert "6.5.0" in manifest
    assert "22.4" in manifest
