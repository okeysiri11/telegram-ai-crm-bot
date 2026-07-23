"""Tests — Freight Marketplace & Global Logistics Network (Sprint 15.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.register import register_port_enterprise_routes
from applications.port_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/port-freight/v1"
WD = "/api/port-warehouse/v1"
CT = "/api/port-customs/v1"
ML = "/api/port-multimodal/v1"
CM = "/api/port-containers/v1"
NAV = "/api/port-navigation/v1"
PE = "/api/port-enterprise/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_enterprise.reset()
    yield
    port_enterprise.reset()


def test_version_freight_ready():
    health = port_enterprise.health()
    assert health["application_version"] == "4.5.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.5.6-enterprise"
    assert health["freight_marketplace_ready"] is True
    assert health["freight_exchange_ready"] is True
    assert health["global_logistics_network_ready"] is True
    assert health["ai_logistics_marketplace_ready"] is True
    assert health["carrier_platform_ready"] is True


def test_marketplace_and_carriers():
    suite = port_enterprise.freight_marketplace
    listing = suite.marketplace.list_cargo(
        title="Test Cargo", origin="A", destination="B", teu=1, price=100
    )
    carrier = suite.carriers.register(name="Test Carrier", carrier_type="truck")
    req = suite.marketplace.transport_request(shipper="S1", origin="A", destination="B")
    suite.marketplace.instant_match(request_id=req["request_id"], carrier_id=carrier["carrier_id"])
    suite.carriers.rate(carrier["carrier_id"], score=4.0)
    assert listing["listing_id"]
    with pytest.raises(ValidationError):
        suite.carriers.register(name="Bad", carrier_type="spaceship")


def test_exchange_network_ai():
    suite = port_enterprise.freight_marketplace
    boot = suite.bootstrap()
    assert boot["booking_id"] and boot["partner_id"] and boot["fraud_id"]
    assert suite.exchange.status()["bookings"] >= 1
    assert suite.network.status()["partners"] >= 1
    assert suite.collaboration.status()["workspaces"] >= 1
    assert suite.ai.status()["recommendations"] >= 1
    with pytest.raises(ValidationError):
        suite.ai.fraud_detect(subject_ref="x", anomaly_score=2.0)
    for dtype in ("marketplace", "carrier", "freight_exchange", "global_network", "ai_marketplace"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_freight(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.5.7-enterprise"
    assert body["freight_marketplace_ready"] is True
    assert body["carrier_platform_ready"] is True

    assert (await client.get(f"{WD}/health")).status == 200
    assert (await client.get(f"{CT}/health")).status == 200
    assert (await client.get(f"{ML}/health")).status == 200
    assert (await client.get(f"{CM}/health")).status == 200
    assert (await client.get(f"{NAV}/health")).status == 200
    assert (await client.get(f"{PE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    book = await client.post(
        f"{PREFIX}/exchange",
        json={
            "action": "book",
            "shipper": "S2",
            "carrier_id": boot_body["carrier_id"],
            "origin": "A",
            "destination": "B",
            "price": 500,
        },
    )
    assert book.status == 201

    ai = await client.post(
        f"{PREFIX}/ai",
        json={"action": "fraud", "subject_ref": boot_body["booking_id"], "anomaly_score": 0.1},
    )
    assert ai.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=carrier")
    assert dash.status == 200


def test_docs_and_regression_15_6():
    for name in (
        "FREIGHT_MARKETPLACE.md",
        "FREIGHT_EXCHANGE.md",
        "GLOBAL_LOGISTICS_NETWORK.md",
        "CARRIER_MANAGEMENT.md",
        "AI_MARKETPLACE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "PORT_FREIGHT.md").exists()
    assert (ROOT / "applications" / "port_enterprise" / "freight_marketplace" / "facade.py").exists()
    assert (ROOT / "applications" / "port_enterprise" / "warehouse_distribution" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "port_enterprise" / "manifest.json").read_text()
    assert "4.5.7-enterprise" in manifest
    assert "15.7" in manifest
