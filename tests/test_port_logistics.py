"""Tests — Port ERP Multimodal Logistics (Sprint 9.5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_erp import port_erp
from applications.port_erp.api.register import register_port_erp_routes
from applications.port_erp.multimodal.models import (
    CarrierContract,
    HubType,
    LogisticsRoute,
    ShippingSchedule,
    TransportBooking,
    TransportMode,
    TransportOrder,
    RouteHub,
)
from applications.port_erp.shared.models import Carrier, Forwarder, ShippingLine


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_erp_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_erp.reset()
    yield
    port_erp.reset()


def test_version_logistics_docs_bridges():
    health = port_erp.health()
    assert health["application_version"] == "2.0.0"
    assert health["logistics_engine"] == "1.0"
    assert "logistics" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "PORT_LOGISTICS.md"
    assert docs.exists()
    assert "Shipping Line Engine" in docs.read_text(encoding="utf-8")
    assert port_erp.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    assert port_erp.ecosystem.ecosystem_health()["ecosystem_dependency"] == "AI Ecosystem v1.5"
    root = Path(__file__).resolve().parents[1] / "applications" / "port_erp"
    for name in (
        "shipping_lines",
        "forwarders",
        "multimodal",
        "rail",
        "road",
        "air",
        "routes",
        "booking",
        "transport_orders",
        "carriers",
        "fleet",
    ):
        assert (root / name).is_dir()


@pytest.mark.asyncio
async def test_shipping_schedules_and_carriers():
    line = port_erp.logistics.shipping.register_line(ShippingLine(name="OceanLine", scac="OCLN"))
    schedule = port_erp.logistics.shipping.create_schedule(
        ShippingSchedule(
            shipping_line_id=line.shipping_line_id,
            service_name="Asia-Africa",
            origin_port="CNSHA",
            destination_port="KEMBA",
            etd=1000,
            eta=2000,
        )
    )
    planned = port_erp.logistics.shipping.plan_voyage(
        schedule.schedule_id, voyage_number="OA001E", vessel_name="Pacific Star"
    )
    assert planned.status.value == "open"
    assert planned.voyage_number == "OA001E"

    carrier = port_erp.logistics.carriers.register(Carrier(name="RoadHaul", mode="truck"))
    contract = port_erp.logistics.carriers.create_contract(
        CarrierContract(
            carrier_id=carrier.carrier_id,
            mode=TransportMode.ROAD,
            rate_per_unit=1.5,
            partner_id=line.shipping_line_id,
        )
    )
    assert contract.rate_per_unit == 1.5
    best = port_erp.logistics.carriers.best_rate(mode=TransportMode.ROAD)
    assert best is not None
    assert best.contract_id == contract.contract_id


@pytest.mark.asyncio
async def test_routes_optimization_and_multimodal():
    origin = port_erp.logistics.routes.create_hub(
        RouteHub(name="Factory", hub_type=HubType.ORIGIN, country="KE")
    )
    port = port_erp.logistics.routes.create_hub(
        RouteHub(name="Mombasa", hub_type=HubType.PORT, country="KE")
    )
    rail = port_erp.logistics.routes.create_hub(
        RouteHub(name="Nairobi Rail", hub_type=HubType.RAIL_TERMINAL, country="KE")
    )
    dest = port_erp.logistics.routes.create_hub(
        RouteHub(name="DC Nairobi", hub_type=HubType.DISTRIBUTION_CENTER, country="KE")
    )

    route = port_erp.logistics.multimodal.plan_door_to_door(
        name="KE door-to-door",
        origin_hub_id=origin.hub_id,
        destination_hub_id=dest.hub_id,
    )
    for kwargs in (
        {"mode": "road", "from_hub_id": origin.hub_id, "to_hub_id": port.hub_id, "distance_km": 50, "duration_hours": 2, "cost": 100},
        {"mode": "sea", "from_hub_id": port.hub_id, "to_hub_id": rail.hub_id, "distance_km": 10, "duration_hours": 5, "cost": 500},
        {"mode": "rail", "from_hub_id": rail.hub_id, "to_hub_id": dest.hub_id, "distance_km": 480, "duration_hours": 12, "cost": 300},
    ):
        leg = port_erp.logistics.routes.build_leg(**kwargs)
        route = port_erp.logistics.routes.add_leg(route.route_id, leg)

    optimized = await port_erp.logistics.routes.optimize(route.route_id, optimize_for="cost")
    assert optimized.optimized_for == "cost"
    assert optimized.total_cost == 900
    assert optimized.door_to_door is True

    order = port_erp.logistics.multimodal.route_container(
        container_id="MSCU1", route_id=route.route_id
    )
    assert order.container_id == "MSCU1"
    transferred = await port_erp.logistics.multimodal.transfer_mode(
        order.order_id, to_mode=TransportMode.RAIL, hub_id=rail.hub_id
    )
    assert transferred.mode == TransportMode.RAIL


@pytest.mark.asyncio
async def test_booking_workflow_and_transport_orders():
    booking = await port_erp.logistics.bookings.create(
        TransportBooking(origin="Mombasa", destination="Rotterdam", mode=TransportMode.SEA)
    )
    assert booking.status.value == "request"
    quoted = port_erp.logistics.bookings.quote(booking.booking_id, amount=2500)
    assert quoted.status.value == "quote"
    port_erp.logistics.bookings.reserve(booking.booking_id)
    confirmed = await port_erp.logistics.bookings.confirm(booking.booking_id, carrier_id="car-1")
    assert confirmed.status.value == "confirmation"
    port_erp.logistics.bookings.execute(booking.booking_id)
    completed = port_erp.logistics.bookings.complete(booking.booking_id)
    assert completed.status.value == "completion"

    cancelable = await port_erp.logistics.bookings.create(
        TransportBooking(origin="A", destination="B")
    )
    cancelled = port_erp.logistics.bookings.cancel(cancelable.booking_id, notes="customer")
    assert cancelled.status.value == "cancellation"

    order = port_erp.logistics.transport.create(
        TransportOrder(origin="Gate", destination="Yard", booking_id=booking.booking_id)
    )
    assigned = await port_erp.logistics.transport.assign(order.order_id, carrier_id="car-1")
    assert assigned.status.value == "assigned"
    port_erp.logistics.fleet.assign_asset(order_id=order.order_id, asset_id="truck-9")
    dispatched = await port_erp.logistics.transport.dispatch(order.order_id)
    assert dispatched.status.value == "dispatched"
    await port_erp.logistics.transport.delay(order.order_id, delay_minutes=30, reason="traffic")
    port_erp.logistics.transport.track(order.order_id, eta=9999)
    done = await port_erp.logistics.transport.complete(order.order_id)
    assert done.status.value == "completed"
    archived = port_erp.logistics.transport.archive(order.order_id)
    assert archived.status.value == "archived"


@pytest.mark.asyncio
async def test_forwarder_consolidation():
    fwd = port_erp.logistics.forwarders.register(Forwarder(name="FastFwd", country="KE"))
    batch = port_erp.logistics.forwarders.consolidate(
        forwarder_id=fwd.forwarder_id,
        booking_ids=["b1", "b2"],
        container_ids=["c1"],
    )
    assert len(batch.booking_ids) == 2
    assert len(port_erp.logistics.forwarders.list_consolidations()) == 1


@pytest.mark.asyncio
async def test_logistics_rest_api(client: TestClient):
    health = await client.get("/api/port/v1/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "2.0.0"
    assert body["logistics_engine"] == "1.0"

    shipping = await client.get("/api/port/v1/shipping")
    assert shipping.status == 200

    line = await client.post("/api/port/v1/shipping/lines", json={"name": "API Line", "scac": "APIL"})
    assert line.status == 201
    line_body = await line.json()

    sched = await client.post(
        "/api/port/v1/shipping/schedules",
        json={
            "shipping_line_id": line_body["shipping_line_id"],
            "origin_port": "A",
            "destination_port": "B",
            "etd": 1,
            "eta": 2,
        },
    )
    assert sched.status == 201

    fwd = await client.post("/api/port/v1/forwarders", json={"name": "API Fwd"})
    assert fwd.status == 201

    carrier = await client.post("/api/port/v1/carriers", json={"name": "API Carrier", "mode": "truck"})
    assert carrier.status == 201

    hub_a = await client.post(
        "/api/port/v1/routes/hubs",
        json={"name": "HubA", "hub_type": "port", "country": "KE"},
    )
    hub_b = await client.post(
        "/api/port/v1/routes/hubs",
        json={"name": "HubB", "hub_type": "warehouse", "country": "KE"},
    )
    a = await hub_a.json()
    b = await hub_b.json()
    route = await client.post(
        "/api/port/v1/routes",
        json={
            "name": "A-B",
            "origin_hub_id": a["hub_id"],
            "destination_hub_id": b["hub_id"],
            "legs": [
                {
                    "mode": "road",
                    "from_hub_id": a["hub_id"],
                    "to_hub_id": b["hub_id"],
                    "distance_km": 20,
                    "duration_hours": 1,
                    "cost": 50,
                }
            ],
        },
    )
    assert route.status == 201
    route_body = await route.json()
    opt = await client.post(
        f"/api/port/v1/routes/{route_body['route_id']}/optimize",
        json={"optimize_for": "eta"},
    )
    assert opt.status == 200

    booking = await client.post(
        "/api/port/v1/bookings",
        json={"origin": "A", "destination": "B", "mode": "sea"},
    )
    assert booking.status == 201
    booking_body = await booking.json()
    quote = await client.post(
        f"/api/port/v1/bookings/{booking_body['booking_id']}/quote",
        json={"amount": 100},
    )
    assert quote.status == 200

    order = await client.post(
        "/api/port/v1/transport",
        json={"origin": "A", "destination": "B", "mode": "road"},
    )
    assert order.status == 201
    order_body = await order.json()
    carrier_body = await carrier.json()
    assigned = await client.post(
        f"/api/port/v1/transport/{order_body['order_id']}/assign",
        json={"carrier_id": carrier_body["carrier_id"]},
    )
    assert assigned.status == 200
