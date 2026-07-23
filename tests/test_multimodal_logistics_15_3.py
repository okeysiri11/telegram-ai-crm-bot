"""Tests — Rail, Truck & Multimodal Logistics (Sprint 15.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.register import register_port_enterprise_routes
from applications.port_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/port-multimodal/v1"
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


def test_version_multimodal_ready():
    health = port_enterprise.health()
    assert health["application_version"] == "4.5.5-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.5.4-enterprise"
    assert health["rail_logistics_ready"] is True
    assert health["truck_logistics_ready"] is True
    assert health["multimodal_platform_ready"] is True
    assert health["shipment_management_ready"] is True
    assert health["ai_logistics_ready"] is True


def test_rail_and_truck():
    suite = port_enterprise.multimodal_logistics
    net = suite.rail.register_network(name="Test Corridor", region="UA")
    train = suite.rail.register_train(name="T1")
    suite.rail.schedule(
        train_id=train["train_id"],
        origin="A",
        destination="B",
        departs_at="2026-08-20T10:00:00Z",
    )
    assert suite.rail.status()["networks"] == 1
    truck = suite.truck.register_truck(plate="TEST1111")
    driver = suite.truck.register_driver(name="Driver A")
    suite.truck.dispatch(
        truck_id=truck["truck_id"], driver_id=driver["driver_id"], destination="Hub"
    )
    assert suite.truck.status()["dispatches"] == 1
    with pytest.raises(ValidationError):
        suite.rail.register_network(name="")
    assert net["network_id"]


def test_shipment_multimodal_ai():
    suite = port_enterprise.multimodal_logistics
    boot = suite.bootstrap()
    assert boot["shipment_id"] and boot["chain_id"] and boot["carbon_id"]
    assert suite.shipments.status()["pods"] >= 1
    assert suite.multimodal.status()["chains"] >= 1
    assert suite.ai.status()["demand_forecasts"] >= 1
    with pytest.raises(ValidationError):
        suite.ai.optimize_route(origin="A", destination="B", mode="teleport")
    for dtype in ("rail", "truck", "multimodal", "shipment", "ai_logistics"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_multimodal(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.5.5-enterprise"
    assert body["rail_logistics_ready"] is True
    assert body["ai_logistics_ready"] is True

    assert (await client.get(f"{CM}/health")).status == 200
    assert (await client.get(f"{NAV}/health")).status == 200
    assert (await client.get(f"{PE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    ship = await client.post(
        f"{PREFIX}/shipments",
        json={"action": "eta", "shipment_id": boot_body["shipment_id"], "hours": 12},
    )
    assert ship.status == 201

    ai = await client.post(
        f"{PREFIX}/ai",
        json={"action": "carbon", "shipment_id": boot_body["shipment_id"], "ton_km": 1000},
    )
    assert ai.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=rail")
    assert dash.status == 200


def test_docs_and_regression_15_3():
    for name in (
        "RAIL_LOGISTICS.md",
        "TRUCK_LOGISTICS.md",
        "MULTIMODAL_TRANSPORT.md",
        "SHIPMENT_MANAGEMENT.md",
        "AI_LOGISTICS.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "PORT_MULTIMODAL.md").exists()
    assert (ROOT / "applications" / "port_enterprise" / "multimodal_logistics" / "facade.py").exists()
    assert (ROOT / "applications" / "port_enterprise" / "container_management" / "facade.py").exists()
    assert (ROOT / "applications" / "port_enterprise" / "navigation" / "facade.py").exists()

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
    assert "4.5.5-enterprise" in manifest
    assert "15.5" in manifest
