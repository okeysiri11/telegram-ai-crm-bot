"""Tests — Enterprise Integration Hub Foundation (Sprint 19.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/enterprise-hub/v1"


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


def test_version_hub_foundation_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.1.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.0.0"
    assert health["enterprise_hub_foundation_ready"] is True
    assert health["integration_layer_ready"] is True
    assert health["enterprise_event_bus_ready"] is True
    assert health["unified_api_ready"] is True
    assert health["engines"]["enterprise_registry"] == "1.0"


def test_registry_and_gateway():
    plat = enterprise_hub.registry.register_platform(name="finance", version="5.2.0-enterprise")
    svc = enterprise_hub.registry.register_service(
        name="finance_api", platform="finance", endpoint="/api/finance-enterprise/v1"
    )
    gw = enterprise_hub.integration.gateway(
        path="/api/finance-enterprise/v1/health", method="GET", target_platform="finance"
    )
    assert plat["platform_id"] and svc["service_id"] and gw["gateway_id"]
    with pytest.raises(ValidationError):
        enterprise_hub.registry.register_platform(name="")


def test_event_bus_bootstrap():
    boot = enterprise_hub.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.1.0"
    assert boot["platform_finance_id"] and boot["event_id"] and boot["replay_id"]
    assert enterprise_hub.events.status()["dead_letters"] >= 1
    for dtype in (
        "overview",
        "platform_status",
        "integration_health",
        "connected_services",
        "environment_status",
    ):
        assert enterprise_hub.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_enterprise_hub(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "6.1.0"
    assert body["enterprise_hub_foundation_ready"] is True
    assert body["unified_api_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    gw = await client.post(
        f"{PREFIX}/integration",
        json={"action": "gateway", "path": "/health", "target_platform": "legal"},
    )
    assert gw.status == 201

    evt = await client.post(
        f"{PREFIX}/events",
        json={"event_type": "hub.ping", "source": "enterprise_hub"},
    )
    assert evt.status == 201
    assert boot_body["organization_id"]


def test_docs_and_regression_19_0():
    for name in (
        "ENTERPRISE_HUB.md",
        "ENTERPRISE_INTEGRATION.md",
        "ENTERPRISE_API_GATEWAY.md",
        "ENTERPRISE_EVENT_BUS.md",
        "ENTERPRISE_ARCHITECTURE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_HUB.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "application.py").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "manifest.json").exists()

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
    assert "6.1.0" in manifest
    assert "22.0" in manifest
    # Finance suite must remain untouched at certified release
    fin_manifest = (ROOT / "applications" / "finance_enterprise" / "manifest.json").read_text()
    assert "5.2.0-enterprise" in fin_manifest
