"""Tests — Warehouse, FEZ & Distribution Centers (Sprint 15.5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.register import register_port_enterprise_routes
from applications.port_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/port-warehouse/v1"
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


def test_version_warehouse_ready():
    health = port_enterprise.health()
    assert health["application_version"] == "4.5.5-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.5.4-enterprise"
    assert health["warehouse_platform_ready"] is True
    assert health["distribution_centers_ready"] is True
    assert health["free_economic_zones_ready"] is True
    assert health["warehouse_automation_ready"] is True
    assert health["ai_warehouse_ready"] is True


def test_warehouse_and_distribution():
    suite = port_enterprise.warehouse_distribution
    wh = suite.warehouse.register_warehouse(name="WH-Test", capacity_teu=1000)
    suite.warehouse.create_zone(warehouse_id=wh["warehouse_id"], name="Z1", zone_type="cold")
    suite.warehouse.receive(warehouse_id=wh["warehouse_id"], sku="S1", qty=10)
    dc = suite.distribution.register_dc(name="DC-Test")
    suite.distribution.fulfill(dc_id=dc["dc_id"], order_ref="O1")
    with pytest.raises(ValidationError):
        suite.warehouse.create_zone(warehouse_id=wh["warehouse_id"], name="Bad", zone_type="orbit")


def test_fez_inventory_automation():
    suite = port_enterprise.warehouse_distribution
    boot = suite.bootstrap()
    assert boot["warehouse_id"] and boot["fez_id"] and boot["agv_id"]
    assert suite.fez.status()["residents"] >= 1
    assert suite.inventory.status()["items"] >= 1
    assert suite.automation.status()["agvs"] >= 1
    assert suite.ai.status()["demand_forecasts"] >= 1
    with pytest.raises(ValidationError):
        suite.inventory.barcode(sku="S", code="")
    for dtype in ("warehouse", "distribution", "fez", "inventory", "ai_warehouse"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_warehouse(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.5.5-enterprise"
    assert body["warehouse_platform_ready"] is True
    assert body["ai_warehouse_ready"] is True

    assert (await client.get(f"{CT}/health")).status == 200
    assert (await client.get(f"{ML}/health")).status == 200
    assert (await client.get(f"{CM}/health")).status == 200
    assert (await client.get(f"{NAV}/health")).status == 200
    assert (await client.get(f"{PE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    auto = await client.post(
        f"{PREFIX}/automation",
        json={"action": "agv", "warehouse_id": boot_body["warehouse_id"], "task": "move"},
    )
    assert auto.status == 201

    ai = await client.post(
        f"{PREFIX}/ai",
        json={"action": "ops", "warehouse_id": boot_body["warehouse_id"]},
    )
    assert ai.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=fez")
    assert dash.status == 200


def test_docs_and_regression_15_5():
    for name in (
        "WAREHOUSE_PLATFORM.md",
        "DISTRIBUTION_CENTERS.md",
        "FREE_ECONOMIC_ZONES.md",
        "WAREHOUSE_AUTOMATION.md",
        "INVENTORY_INTELLIGENCE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "PORT_WAREHOUSE.md").exists()
    assert (ROOT / "applications" / "port_enterprise" / "warehouse_distribution" / "facade.py").exists()
    assert (ROOT / "applications" / "port_enterprise" / "customs_trade" / "facade.py").exists()

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
