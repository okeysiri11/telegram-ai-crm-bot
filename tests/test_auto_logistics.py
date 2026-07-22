"""Tests — Auto Marketplace Logistics (Sprint 10.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.transport.models import (
    Carrier,
    CarrierKind,
    CustomsDeclaration,
    FleetMovement,
    ShipmentKind,
    TradeShipment,
    TransportMode,
    VehicleShipment,
)


VIN = "JTDBR32E720123456"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()


def test_version_modules_docs_bridges():
    health = auto_marketplace.health()
    assert health["application_version"] == "1.6.0-alpha"
    assert health["transport_engine"] == "1.0"
    assert health["tracking_engine"] == "1.0"
    assert health["customs_engine"] == "1.0"
    assert "logistics" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "AUTO_LOGISTICS.md"
    assert docs.exists() and "1.6.0-alpha" in docs.read_text(encoding="utf-8")
    assert "1.6.0-alpha" in (Path(__file__).resolve().parents[1] / "docs" / "AUTO_MARKETPLACE.md").read_text(
        encoding="utf-8"
    )
    assert auto_marketplace.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    root = Path(__file__).resolve().parents[1] / "applications" / "auto_marketplace"
    for name in (
        "transport",
        "vehicle_shipping",
        "carriers",
        "dispatch",
        "tracking",
        "customs",
        "import_export",
        "international",
        "route_optimizer",
        "delivery",
        "fleet_transport",
        "documents",
    ):
        assert (root / name).is_dir()


def test_transport_engine():
    shipment = auto_marketplace.logistics.transport.create(
        VehicleShipment(
            vehicle_id="v1",
            vin=VIN,
            kind=ShipmentKind.DEALER_TRANSFER,
            mode=TransportMode.TRUCK,
            origin="Munich",
            destination="Hamburg",
            origin_country="DE",
            destination_country="DE",
        )
    )
    booked = auto_marketplace.logistics.transport.book(shipment.shipment_id)
    assert booked.status.value == "booked"
    assert booked.tracking_id
    assert booked.document_ids
    carrier = auto_marketplace.logistics.carriers.register(
        Carrier(name="EuroHaul", kind=CarrierKind.COMPANY, modes=["truck"], rating=4.5, countries=["DE"])
    )
    auto_marketplace.logistics.dispatch.dispatch(shipment.shipment_id, carrier_id=carrier.carrier_id, driver_id="d1")
    transit = auto_marketplace.logistics.transport.start_transit(shipment.shipment_id)
    assert transit.status.value == "in_transit"
    delivered = auto_marketplace.logistics.delivery.complete(shipment.shipment_id)
    assert delivered["status"] == "delivered"
    pred = auto_marketplace.logistics.transport.ai_delivery_prediction(shipment.shipment_id)
    assert "predicted_delivery" in pred
    assert auto_marketplace.logistics.transport.ai_delay_forecast(shipment.shipment_id)["risk_level"]
    assert auto_marketplace.logistics.transport.ai_risk_prediction(shipment.shipment_id)["risk_score"] >= 0


def test_tracking_engine():
    shipment = auto_marketplace.logistics.transport.create(
        VehicleShipment(vehicle_id="v2", origin="A", destination="B", vin=VIN)
    )
    booked = auto_marketplace.logistics.transport.book(shipment.shipment_id)
    session = auto_marketplace.logistics.tracking.get(booked.tracking_id)
    auto_marketplace.logistics.tracking.add_geofence(
        session.tracking_id, name="depot", lat=52.5, lon=13.4, radius_deg=0.1
    )
    updated = auto_marketplace.logistics.tracking.update_gps(session.tracking_id, lat=52.52, lon=13.41)
    assert updated.route_history
    eta = auto_marketplace.logistics.tracking.predict_eta(session.tracking_id)
    assert "eta" in eta
    assert auto_marketplace.logistics.tracking.timeline(session.tracking_id)


def test_import_export_and_customs():
    trade = auto_marketplace.logistics.import_export.create_trade(
        TradeShipment(
            direction="import",
            vehicle_id="v1",
            vin=VIN,
            origin_country="JP",
            destination_country="US",
        ),
        vehicle_value=25000,
    )
    assert trade.duties > 0
    assert trade.certificates
    approved = auto_marketplace.logistics.import_export.approve(trade.trade_id)
    assert approved.status == "approved"

    export = auto_marketplace.logistics.import_export.create_trade(
        TradeShipment(
            direction="export",
            vehicle_id="v2",
            vin=VIN,
            origin_country="DE",
            destination_country="TR",
        ),
        vehicle_value=18000,
    )
    assert export.permissions

    declaration = auto_marketplace.logistics.customs.create(
        CustomsDeclaration(shipment_id="s1", vin=VIN, checkpoint="DE-PL")
    )
    assert declaration.vin_valid
    auto_marketplace.logistics.customs.assign_broker(
        declaration.customs_id, broker_id="br1", broker_name="ClearFast"
    )
    submitted = auto_marketplace.logistics.customs.submit(declaration.customs_id)
    assert submitted.status == "submitted"
    cleared = auto_marketplace.logistics.customs.clear(declaration.customs_id)
    assert cleared.status == "cleared"
    advice = auto_marketplace.logistics.customs.assistant_advice(declaration.customs_id)
    assert advice["ai_advice"]


def test_carriers_routes_fleet():
    carrier = auto_marketplace.logistics.carriers.register(
        Carrier(name="SeaLink", kind=CarrierKind.SEA, modes=["sea"], rating=4.0, countries=["US", "EU"])
    )
    auto_marketplace.logistics.carriers.add_driver(carrier.carrier_id, name="Capt. A", license_id="M1")
    rated = auto_marketplace.logistics.carriers.rate(carrier.carrier_id, 5.0)
    assert rated.rating > 0
    assert auto_marketplace.logistics.carriers.recommend(mode="sea")

    route = auto_marketplace.logistics.routes.optimize(
        origin="Rotterdam",
        destination="Gdansk",
        stops=[{"name": "Berlin"}],
        border_crossings=["NL-DE", "DE-PL"],
        weather_factor=1.1,
        traffic_factor=1.2,
    )
    assert route.distance_km > 0
    assert route.ai_notes

    movement = auto_marketplace.logistics.fleet.plan(
        FleetMovement(
            kind="auction",
            vehicle_ids=["v1", "v2"],
            from_location="Auction Yard",
            to_location="Dealer Lot",
            carrier_id=carrier.carrier_id,
        )
    )
    scheduled = auto_marketplace.logistics.fleet.schedule_truck(movement.movement_id, departure=1.0, trucks=2)
    assert scheduled.status == "scheduled"


@pytest.mark.asyncio
async def test_logistics_api_routes(client: TestClient):
    health = await client.get("/api/auto/v1/health")
    body = await health.json()
    assert body["application_version"] == "1.6.0-alpha"
    assert body["transport_engine"] == "1.0"

    create = await client.post(
        "/api/auto/v1/transport/shipments",
        json={"vehicle_id": "v1", "origin": "A", "destination": "B", "vin": VIN},
    )
    assert create.status == 201
    sid = (await create.json())["shipment_id"]
    book = await client.post(f"/api/auto/v1/transport/shipments/{sid}/book")
    assert book.status == 200
    tracking_id = (await book.json())["tracking_id"]

    gps = await client.post(f"/api/auto/v1/tracking/{tracking_id}/gps", json={"lat": 50.0, "lon": 10.0})
    assert gps.status == 200

    carrier = await client.post("/api/auto/v1/carriers", json={"name": "API Haul", "kind": "tow", "modes": ["tow"]})
    assert carrier.status == 201

    imp = await client.post(
        "/api/auto/v1/import",
        json={"vehicle_id": "v1", "origin_country": "JP", "destination_country": "US", "vehicle_value": 20000, "vin": VIN},
    )
    assert imp.status == 201

    exp = await client.post(
        "/api/auto/v1/export",
        json={"vehicle_id": "v2", "origin_country": "DE", "destination_country": "AE", "vehicle_value": 15000, "vin": VIN},
    )
    assert exp.status == 201

    customs = await client.post("/api/auto/v1/customs", json={"shipment_id": sid, "vin": VIN})
    assert customs.status == 201


def test_platform_untouched():
    root = Path(__file__).resolve().parents[1]
    assert (root / "applications" / "auto_marketplace" / "transport").is_dir()
    assert not (root / "platform_ai" / "transport").exists()
    assert (root / "applications" / "auto_marketplace" / "customs" / "engine.py").exists()
