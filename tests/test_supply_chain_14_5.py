"""Tests — Agro Supply Chain, Elevators, Warehouses & Export (Sprint 14.5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from applications.agro_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/agro-supply-chain/v1"
CE = "/api/controlled-environment/v1"
CA = "/api/crop-ai/v1"
SI = "/api/smart-irrigation/v1"
PA = "/api/precision-agriculture/v1"
AE = "/api/agro-enterprise/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    agro_enterprise.reset()
    yield
    agro_enterprise.reset()


def test_version_supply_chain_ready():
    health = agro_enterprise.health()
    assert health["application_version"] == "4.3.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.3.6-enterprise"
    assert health["supply_chain_ready"] is True
    assert health["grain_elevator_ready"] is True
    assert health["warehouse_platform_ready"] is True
    assert health["export_logistics_ready"] is True
    assert health["trading_platform_ready"] is True


def test_supply_warehouse_elevator():
    suite = agro_enterprise.supply_chain
    elev = suite.elevator.register_elevator(name="E1", location="Kyiv")
    silo = suite.elevator.register_silo(elevator_id=elev["elevator_id"], capacity_t=1000)
    suite.elevator.intake(silo["silo_id"], tons=400)
    with pytest.raises(ValidationError):
        suite.elevator.intake(silo["silo_id"], tons=700)
    wh = suite.warehouse.register_warehouse(name="WH1")
    inv = suite.warehouse.add_inventory(warehouse_id=wh["warehouse_id"], sku="CORN", tons=50)
    assert inv["barcode"] and inv["rfid"]
    insp = suite.quality.inspect(lot_id=inv["lot"], moisture_pct=16, foreign_material_pct=3)
    assert insp["classification"] == "B"


def test_export_trading_logistics():
    suite = agro_enterprise.supply_chain
    boot = suite.bootstrap()
    assert boot["contract_id"]
    assert boot["desk_order_id"]
    route = suite.logistics.optimize_route(origin="A", destination="B", mode="rail")
    assert route["eta_hours"] == 36
    with pytest.raises(ValidationError):
        suite.export.create_contract(buyer="X", commodity="wheat", tons=1, price=1, incoterm="ZZZ")
    for dtype in ("supply_chain", "warehouse", "elevator", "export", "trading", "logistics"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_supply_chain(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.3.7-enterprise"
    assert body["supply_chain_ready"] is True
    assert body["trading_platform_ready"] is True

    assert (await client.get(f"{CE}/health")).status == 200
    assert (await client.get(f"{CA}/health")).status == 200
    assert (await client.get(f"{SI}/health")).status == 200
    assert (await client.get(f"{PA}/health")).status == 200
    assert (await client.get(f"{AE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    quality = await client.post(
        f"{PREFIX}/quality",
        json={"lot_id": "LOT-X", "moisture_pct": 13, "protein_pct": 13},
    )
    assert quality.status == 201

    export = await client.post(
        f"{PREFIX}/export",
        json={"action": "docs", "contract_id": boot_body["contract_id"]},
    )
    assert export.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=export")
    assert dash.status == 200


def test_docs_and_regression_14_5():
    for name in (
        "AGRO_SUPPLY_CHAIN.md",
        "GRAIN_ELEVATOR.md",
        "WAREHOUSE_MANAGEMENT.md",
        "EXPORT_LOGISTICS.md",
        "GRAIN_QUALITY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AGRO_SUPPLY_CHAIN.md").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "supply_chain" / "facade.py").exists()
    for pkg in ("controlled_environment", "crop_ai", "smart_irrigation", "precision_agriculture"):
        assert (ROOT / "applications" / "agro_enterprise" / pkg / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_marketplace.config import DEFAULT_CONFIG as AGRO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "agro_enterprise" / "manifest.json").read_text()
    assert "4.3.7-enterprise" in manifest
    assert "14.7" in manifest
