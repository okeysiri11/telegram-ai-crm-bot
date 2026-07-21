"""Tests — Port ERP Tracking (Sprint 9.2)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_erp import port_erp
from applications.port_erp.api.register import register_port_erp_routes
from applications.port_erp.shared.models import Container, ContainerStatus, GeofenceType, Vessel
from applications.port_erp.tracking.models import Geofence, TruckTrack


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


def test_version_tracking_engine_and_docs():
    health = port_erp.health()
    assert health["application_version"] == "1.1.0-alpha"
    assert health["tracking_engine"] == "1.0"
    assert "tracking" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "PORT_TRACKING.md"
    assert docs.exists()
    assert "AIS Tracking Engine" in docs.read_text(encoding="utf-8")


def test_bridges_platform_core_untouched():
    assert port_erp.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    assert port_erp.ecosystem.ecosystem_health()["ecosystem_dependency"] == "AI Ecosystem v1.5"
    root = Path(__file__).resolve().parents[1]
    # Bridges exist inside port_erp only
    assert (root / "applications" / "port_erp" / "integrations" / "platform_bridge.py").exists()
    assert (root / "applications" / "port_erp" / "integrations" / "ecosystem_bridge.py").exists()
    # Tracking modules live under port_erp
    for name in ("tracking", "ais", "gps", "fleet", "geofence", "maps", "timeline"):
        assert (root / "applications" / "port_erp" / name).is_dir()


@pytest.mark.asyncio
async def test_ais_live_vessel_tracking_and_timeline():
    vessel = port_erp.core.vessels.register(Vessel(name="Atlantic Pearl", imo="9300001"))
    live = await port_erp.tracking.ais.update_vessel_position(
        vessel.vessel_id,
        latitude=-4.05,
        longitude=39.68,
        speed_knots=12.5,
        heading_deg=85.0,
        destination="Mombasa",
        last_checkpoint="Approach Buoy",
    )
    assert live.asset_id == vessel.vessel_id
    assert live.position.speed_knots == 12.5
    assert live.destination == "Mombasa"
    assert live.last_checkpoint == "Approach Buoy"
    assert live.source == "ais"

    again = await port_erp.tracking.ais.update_vessel_position(
        vessel.vessel_id,
        latitude=-4.04,
        longitude=39.67,
        speed_knots=10.0,
        heading_deg=80.0,
        destination="Mombasa",
        last_checkpoint="Pilot Station",
    )
    assert again.position.latitude == -4.04
    history = port_erp.tracking.live.route_history("vessel", vessel.vessel_id)
    assert history is not None
    assert len(history.points) >= 2
    summary = port_erp.tracking.routes.summary("vessel", vessel.vessel_id)
    assert summary["speed_knots"] == 10.0
    assert summary["heading_deg"] == 80.0

    events = port_erp.tracking.timeline.for_asset("vessel", vessel.vessel_id)
    assert any(e.event_type == "position_updated" for e in events)


@pytest.mark.asyncio
async def test_eta_prediction_and_delay():
    vessel = port_erp.core.vessels.register(Vessel(name="Indian Star", imo="9300002"))
    await port_erp.tracking.ais.update_vessel_position(
        vessel.vessel_id,
        latitude=-4.20,
        longitude=39.90,
        speed_knots=8.0,
        destination="Mombasa CT1",
    )
    planned = time.time() + 3600  # 1 hour plan — will be behind at 8kn over ~20nm
    pred = await port_erp.tracking.eta.predict_arrival(
        asset_type="vessel",
        asset_id=vessel.vessel_id,
        dest_lat=-4.05,
        dest_lon=39.68,
        destination="Mombasa CT1",
        planned_eta=planned,
    )
    assert pred.eta > time.time()
    assert pred.confidence >= 0.5
    assert pred.destination == "Mombasa CT1"
    etd = port_erp.tracking.eta.calculate_etd(asset_type="vessel", asset_id=vessel.vessel_id)
    assert etd > time.time()


@pytest.mark.asyncio
async def test_container_lifecycle_and_history():
    container = port_erp.core.containers.register(Container(container_number="MSCU5555555"))
    assert container.status == ContainerStatus.CREATED

    for status in (
        ContainerStatus.BOOKED,
        ContainerStatus.LOADED,
        ContainerStatus.AT_PORT,
        ContainerStatus.ON_VESSEL,
        ContainerStatus.IN_TRANSIT,
        ContainerStatus.ARRIVED,
        ContainerStatus.WAREHOUSE,
        ContainerStatus.OUT_FOR_DELIVERY,
        ContainerStatus.DELIVERED,
        ContainerStatus.COMPLETED,
    ):
        updated = await port_erp.tracking.containers.advance(
            container.container_id, status, location=status.value
        )
        assert updated.status.value == status.value

    history = port_erp.tracking.containers.history(container.container_id)
    assert len(history) >= 10
    assert history[-1].to_status == "completed"
    statuses = port_erp.tracking.containers.statuses()
    assert "created" in statuses
    assert "completed" in statuses
    assert len(statuses) == 13


@pytest.mark.asyncio
async def test_truck_gps_geofence_and_fleet():
    truck = port_erp.tracking.trucks.register_truck(TruckTrack(plate_number="KCA123A"))
    fence = port_erp.tracking.geofences.create(
        Geofence(
            name="Gate North",
            fence_type=GeofenceType.GATE,
            center_lat=-4.05,
            center_lon=39.68,
            radius_m=1000.0,
        )
    )
    assert fence.fence_type == GeofenceType.GATE

    inside = await port_erp.tracking.trucks.update_position(
        truck.truck_id,
        latitude=-4.05,
        longitude=39.68,
        speed_knots=5.0,
        last_checkpoint="Gate North",
    )
    assert inside.asset_id == truck.truck_id

    outside = await port_erp.tracking.trucks.update_position(
        truck.truck_id,
        latitude=-5.0,
        longitude=40.0,
        speed_knots=20.0,
    )
    assert outside.position.latitude == -5.0

    rail = await port_erp.tracking.fleet.update_rail_position(
        "rail-1",
        latitude=-4.06,
        longitude=39.70,
        speed_knots=30.0,
        destination="Rail Terminal",
    )
    assert rail.asset_type.value == "rail"

    snap = port_erp.tracking.fleet.snapshot()
    assert len(snap["trucks"]) >= 1
    assert len(snap["rail"]) >= 1
    assert len(snap["registered_trucks"]) == 1

    viewport = port_erp.tracking.maps.viewport(center_lat=-4.05, center_lon=39.68)
    assert "geofences" in viewport
    assert "assets" in viewport

    dash = port_erp.live_operations.dashboard()
    assert dash["tracking_engine"] == "1.0"
    assert dash["metrics"]["trucks"] >= 1


@pytest.mark.asyncio
async def test_tracking_rest_api(client: TestClient):
    health = await client.get("/api/port/v1/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "1.1.0-alpha"
    assert body["tracking_engine"] == "1.0"

    tracking = await client.get("/api/port/v1/tracking")
    assert tracking.status == 200
    assert (await tracking.json())["tracking_engine"] == "1.0"

    vessel_resp = await client.post(
        "/api/port/v1/vessels",
        json={"name": "API Vessel", "imo": "9400001"},
    )
    assert vessel_resp.status == 201
    vessel = await vessel_resp.json()

    pos = await client.post(
        f"/api/port/v1/vessels/{vessel['vessel_id']}/position",
        json={
            "latitude": -4.05,
            "longitude": 39.68,
            "speed_knots": 11,
            "heading_deg": 90,
            "destination": "Port",
        },
    )
    assert pos.status == 200

    cont_resp = await client.post(
        "/api/port/v1/containers",
        json={"container_number": "APIU1111111"},
    )
    container = await cont_resp.json()
    life = await client.post(
        f"/api/port/v1/containers/{container['container_id']}/lifecycle",
        json={"status": "booked", "location": "booking desk"},
    )
    assert life.status == 200
    assert (await life.json())["status"] == "booked"

    truck_resp = await client.post("/api/port/v1/gps/trucks", json={"plate_number": "KBB999Z"})
    assert truck_resp.status == 201
    truck = await truck_resp.json()
    gps = await client.post(
        f"/api/port/v1/gps/trucks/{truck['truck_id']}/position",
        json={"latitude": -4.05, "longitude": 39.68, "speed_knots": 4},
    )
    assert gps.status == 200

    maps = await client.get("/api/port/v1/maps")
    assert maps.status == 200
    timeline = await client.get("/api/port/v1/timeline")
    assert timeline.status == 200
    assert len((await timeline.json())["items"]) >= 1

    eta = await client.post(
        "/api/port/v1/tracking/eta",
        json={
            "asset_type": "vessel",
            "asset_id": vessel["vessel_id"],
            "dest_lat": -4.06,
            "dest_lon": 39.67,
            "destination": "Berth 1",
        },
    )
    assert eta.status == 200
    assert "eta" in await eta.json()
