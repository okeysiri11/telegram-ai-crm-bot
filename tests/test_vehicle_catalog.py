"""Tests — Vehicle Catalog & Inventory Engine (Sprint 6.2)."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.filters.criteria import VehicleSearchCriteria
from applications.auto_marketplace.media.models import MediaType, VehicleMedia
from applications.auto_marketplace.specifications.models import FuelType, InventoryVehicleStatus
from applications.auto_marketplace.vehicle_catalog.models import CatalogVehicle
from applications.auto_marketplace.vehicle_catalog.vin_validator import validate_vin


VALID_VIN = "1HGCM82633A004352"


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


def test_vin_validation():
    ok, _ = validate_vin(VALID_VIN)
    assert ok
    ok, msg = validate_vin("INVALID")
    assert not ok


@pytest.mark.asyncio
async def test_catalog_crud():
    vehicle = CatalogVehicle(
        vin=VALID_VIN,
        brand="Honda",
        model="Accord",
        year=2021,
        price=24000,
        dealer_id="d1",
    )
    created = await auto_marketplace.vehicle_catalog.create(vehicle)
    assert created.vehicle_id
    assert created.category
    assert created.tags

    fetched = auto_marketplace.vehicle_catalog.get(created.vehicle_id)
    assert fetched.brand == "Honda"


@pytest.mark.asyncio
async def test_bulk_import_and_archive():
    vehicles = [
        CatalogVehicle(brand="Toyota", model="Camry", year=2020, price=20000, dealer_id="d1"),
        CatalogVehicle(brand="Toyota", model="Corolla", year=2019, price=15000, dealer_id="d1"),
    ]
    result = await auto_marketplace.vehicle_catalog.bulk_import(vehicles)
    assert result["created"] == 2

    vid = result["items"][0]["vehicle_id"]
    archived = await auto_marketplace.vehicle_catalog.archive(vid)
    assert archived.status == InventoryVehicleStatus.ARCHIVED

    restored = await auto_marketplace.vehicle_catalog.restore(vid)
    assert restored.status == InventoryVehicleStatus.AVAILABLE


@pytest.mark.asyncio
async def test_duplicate_detection():
    v1 = await auto_marketplace.vehicle_catalog.create(
        CatalogVehicle(vin=VALID_VIN, brand="Honda", model="Civic", year=2020, mileage_km=10000, dealer_id="d1")
    )
    v2 = CatalogVehicle(vin=VALID_VIN, brand="Honda", model="Civic", year=2020, mileage_km=10000, dealer_id="d1")
    created2 = await auto_marketplace.vehicle_catalog.create(v2)
    assert created2.duplicate_of == v1.vehicle_id


@pytest.mark.asyncio
async def test_inventory_lifecycle():
    vehicle = await auto_marketplace.vehicle_catalog.create(
        CatalogVehicle(brand="BMW", model="X3", year=2022, price=45000, dealer_id="d1")
    )
    await auto_marketplace.inventory_engine.mark_incoming(vehicle.vehicle_id, warehouse_id="wh1")
    await auto_marketplace.inventory_engine.mark_available(vehicle.vehicle_id)
    await auto_marketplace.inventory_engine.mark_listed(vehicle.vehicle_id)
    await auto_marketplace.inventory_engine.reserve(
        vehicle.vehicle_id,
        reservation_id="r1",
        customer_id="c1",
    )
    await auto_marketplace.inventory_engine.mark_sold(vehicle.vehicle_id, deal_id="deal1", final_price=44000)

    availability = auto_marketplace.inventory_engine.availability(dealer_id="d1")
    assert availability["sold"] >= 1


@pytest.mark.asyncio
async def test_media_upload_and_reorder():
    vehicle = await auto_marketplace.vehicle_catalog.create(
        CatalogVehicle(brand="Audi", model="A4", year=2023, price=38000, dealer_id="d1")
    )
    m1 = await auto_marketplace.media.upload(
        VehicleMedia(vehicle_id=vehicle.vehicle_id, url="https://cdn/1.jpg", media_type=MediaType.PHOTO)
    )
    m2 = await auto_marketplace.media.upload(
        VehicleMedia(vehicle_id=vehicle.vehicle_id, url="https://cdn/2.jpg", media_type=MediaType.PHOTO)
    )
    reordered = await auto_marketplace.media.reorder(vehicle.vehicle_id, [m2.media_id, m1.media_id])
    assert reordered[0].media_id == m2.media_id

    optimized = auto_marketplace.media.optimize(m1.media_id)
    assert optimized.optimized


@pytest.mark.asyncio
async def test_search_engine_filters():
    await auto_marketplace.vehicle_catalog.create(
        CatalogVehicle(
            brand="Tesla",
            model="Model 3",
            year=2023,
            price=42000,
            mileage_km=5000,
            dealer_id="d1",
            fuel_type=FuelType.ELECTRIC,
        )
    )
    criteria = VehicleSearchCriteria(brand="Tesla", fuel_type=FuelType.ELECTRIC, price_max=50000)
    results = await auto_marketplace.search_engine.search(criteria)
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_catalog_api_create(client: TestClient):
    resp = await client.post(
        "/api/auto/v1/catalog/vehicles",
        json={"brand": "Ford", "model": "Focus", "year": 2019, "price": 12000, "dealer_id": "d1"},
    )
    assert resp.status == 201


@pytest.mark.asyncio
async def test_catalog_search_api(client: TestClient):
    await client.post(
        "/api/auto/v1/catalog/vehicles",
        json={"brand": "Mazda", "model": "CX-5", "year": 2021, "price": 28000, "dealer_id": "d1"},
    )
    resp = await client.get("/api/auto/v1/catalog/search", params={"brand": "Mazda"})
    assert resp.status == 200
    data = await resp.json()
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_vehicle_added_event():
    received: list = []

    from events import subscribe

    subscribe("VehicleAddedEvent", lambda e: received.append(e))
    await auto_marketplace.vehicle_catalog.create(
        CatalogVehicle(brand="Volvo", model="XC60", year=2022, price=50000, dealer_id="d1")
    )
    await asyncio.sleep(0.05)
    assert len(received) >= 1
