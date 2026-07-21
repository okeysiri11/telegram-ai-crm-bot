"""Tests — Export, Logistics & International Trade (Sprint 8.5)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.register import register_agro_marketplace_routes
from applications.agro_marketplace.product_catalog.models import AgroWarehouse
from applications.agro_marketplace.export.models import (
    Carrier,
    IncotermCode,
    InsurancePolicy,
    InternationalExportShipment,
    ShipmentItem,
)


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    agro_marketplace.reset()
    yield
    agro_marketplace.reset()


def test_version_and_incoterms():
    health = agro_marketplace.health()
    assert health["application_version"] == "1.5.0-alpha"
    assert health["export_engine"] == "1.0"
    codes = {i.code.value for i in agro_marketplace.incoterms.list_incoterms()}
    assert codes == {"FOB", "CIF", "CFR", "DAP", "EXW", "DDP"}
    ports = agro_marketplace.ports.list_ports()
    assert len(ports) >= 4


@pytest.mark.asyncio
async def test_export_lifecycle():
    origin = agro_marketplace.ports.list_ports(country="KE")[0]
    dest = agro_marketplace.ports.list_ports(country="NL")[0]
    carrier = agro_marketplace.shipping.create_carrier(
        Carrier(name="SeaAgro", countries=["NL", "AE"], rating=4.8, mode="sea")
    )
    shipment = await agro_marketplace.export_engine.create_shipment(
        InternationalExportShipment(
            order_id="ord-1",
            exporter_id="exp-1",
            buyer_id="buy-1",
            origin_country="KE",
            destination_country="NL",
            origin_port_id=origin.port_id,
            destination_port_id=dest.port_id,
            carrier_id=carrier.carrier_id,
            incoterm=IncotermCode.CIF,
        )
    )
    assert shipment.status.value == "planned"

    item = agro_marketplace.export_engine.add_item(
        ShipmentItem(
            shipment_id=shipment.shipment_id,
            product_id="maize",
            description="Yellow maize",
            quantity=20,
            unit_value=250,
            hs_code="1005.90",
        )
    )
    assert item.quantity == 20

    docs = await agro_marketplace.export_engine.prepare_documents(
        shipment.shipment_id, cargo_value=5000
    )
    assert len(docs) >= 5
    verify = await agro_marketplace.export_engine.verify_documents(shipment.shipment_id)
    assert "valid" in verify

    risk = await agro_marketplace.export_engine.assess_risk(shipment.shipment_id)
    assert "risk_score" in risk

    dispatched = await agro_marketplace.export_engine.dispatch(shipment.shipment_id)
    assert dispatched.status.value == "dispatched"

    arrived = await agro_marketplace.export_engine.arrive_port(shipment.shipment_id)
    assert arrived.status.value == "port_arrived"

    customs = await agro_marketplace.export_engine.clear_customs(shipment.shipment_id)
    assert customs["declaration"]["status"] == "cleared"

    delivered = await agro_marketplace.export_engine.confirm_delivery(shipment.shipment_id)
    assert delivered.status.value == "delivered"

    completed = await agro_marketplace.export_engine.complete_export(shipment.shipment_id)
    assert completed.status.value == "completed"

    timeline = agro_marketplace.tracking.timeline(shipment.shipment_id)
    types = {e.event_type for e in timeline}
    assert "created" in types
    assert "dispatched" in types
    assert "export_completed" in types


@pytest.mark.asyncio
async def test_logistics_plan_and_dispatch():
    origin = agro_marketplace.ports.list_ports(country="KE")[0]
    dest = agro_marketplace.ports.list_ports(country="NL")[0]
    agro_marketplace.shipping.create_carrier(
        Carrier(name="FreightKE", countries=["NL"], rating=4.2)
    )
    warehouse = await agro_marketplace.warehouse_engine.create_warehouse(
        AgroWarehouse(name="Nairobi Hub", region="Nairobi", capacity_tons=500, used_tons=100)
    )
    plan = await agro_marketplace.logistics_engine.plan_shipment(
        InternationalExportShipment(
            origin_country="KE",
            destination_country="NL",
            origin_port_id=origin.port_id,
            destination_port_id=dest.port_id,
            warehouse_id=warehouse.warehouse_id,
            exporter_id="exp-2",
            incoterm=IncotermCode.FOB,
        )
    )
    shipment_id = plan["shipment"]["shipment_id"]
    assert plan["carriers"]
    assert plan["delivery_prediction"]["predicted_transit_days"] > 0

    result = await agro_marketplace.logistics_engine.warehouse_dispatch(
        shipment_id=shipment_id,
        warehouse_id=warehouse.warehouse_id,
        quantity_tons=10,
        product_id="maize",
    )
    assert result["load"]["sealed"] is True
    assert result["container"]["status"] == "loaded"


@pytest.mark.asyncio
async def test_api_export_health_and_flow(client: TestClient):
    resp = await client.get("/api/agro/v1/export/health")
    assert resp.status == 200
    body = await resp.json()
    assert body["export_engine"] == "1.0"
    assert body["application_version"] == "1.5.0-alpha"

    incoterms = await client.get("/api/agro/v1/export/incoterms")
    assert incoterms.status == 200
    assert len((await incoterms.json())["items"]) == 6

    ports = await client.get("/api/agro/v1/logistics/ports")
    assert ports.status == 200
    port_items = (await ports.json())["items"]
    assert len(port_items) >= 4

    carrier_resp = await client.post(
        "/api/agro/v1/logistics/carriers",
        json={"name": "API Carrier", "countries": ["AE"], "rating": 4.0},
    )
    assert carrier_resp.status == 201
    carrier = await carrier_resp.json()

    create = await client.post(
        "/api/agro/v1/export/shipments",
        json={
            "destination_country": "AE",
            "origin_country": "KE",
            "origin_port_id": port_items[0]["port_id"],
            "destination_port_id": next(p["port_id"] for p in port_items if p["country"] == "AE"),
            "carrier_id": carrier["carrier_id"],
            "incoterm": "FOB",
            "exporter_id": "exp-api",
        },
    )
    assert create.status == 201
    shipment = await create.json()
    sid = shipment["shipment_id"]

    docs = await client.post(f"/api/agro/v1/export/shipments/{sid}/documents", json={"cargo_value": 1000})
    assert docs.status == 200

    track = await client.get(f"/api/agro/v1/tracking/{sid}")
    assert track.status == 200
    assert len((await track.json())["items"]) >= 1

    dispatch = await client.post(f"/api/agro/v1/export/shipments/{sid}/dispatch", json={})
    assert dispatch.status == 200


@pytest.mark.asyncio
async def test_insurance_finance_and_opportunities():
    shipment = await agro_marketplace.export_engine.create_shipment(
        InternationalExportShipment(destination_country="NL", origin_country="KE", exporter_id="e1")
    )
    policy = agro_marketplace.insurance.create_policy(
        InsurancePolicy(
            shipment_id=shipment.shipment_id,
            insurer="AgriCover",
            coverage_amount=100000,
        )
    )
    assert policy.premium > 0
    finance = agro_marketplace.freight_finance.estimate(
        shipment_id=shipment.shipment_id,
        freight_cost=4200,
        coverage_amount=100000,
        cargo_value=80000,
    )
    assert finance.total > 4200
    opps = await agro_marketplace.export_ai.trade_opportunities("NL")
    assert opps[0]["destination_country"] == "NL"
