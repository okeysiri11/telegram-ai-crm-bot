"""Tests — Agro Catalog, Warehouse & Inventory (Sprint 8.2)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.register import register_agro_marketplace_routes
from applications.agro_marketplace.product_catalog.models import (
    AgriculturalProduct,
    AgroWarehouse,
    HarvestBatch,
    HarvestRecord,
    QualityCertificateRecord,
    Season,
    StorageLocation,
    StorageLotRecord,
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


@pytest.mark.asyncio
async def test_product_catalog_crud_bulk_archive():
    product = await agro_marketplace.product_catalog.create(
        AgriculturalProduct(name="Maize Grade A", region="Nairobi", quantity=50, price=175)
    )
    assert product.sku
    assert product.category_id  # auto-categorized

    updated = await agro_marketplace.product_catalog.update(product.product_id, price=180)
    assert updated.price == 180

    imported = await agro_marketplace.product_catalog.bulk_import(
        [
            AgriculturalProduct(name="Wheat Soft", region="Nakuru", quantity=20, price=200),
            AgriculturalProduct(name="Barley", region="Nakuru", quantity=10, price=150),
        ]
    )
    assert len(imported) == 2

    archived = await agro_marketplace.product_catalog.archive(product.product_id)
    assert archived.status.value == "archived"
    restored = await agro_marketplace.product_catalog.restore(product.product_id)
    assert restored.status.value == "available"

    agro_marketplace.product_catalog.set_attributes(product.product_id, {"organic": True})
    assert agro_marketplace.product_catalog.get(product.product_id).attributes["organic"] is True


@pytest.mark.asyncio
async def test_duplicate_detection():
    first = await agro_marketplace.product_catalog.create(
        AgriculturalProduct(name="Coffee Arabica", sku="COF-1", farmer_id="f1", crop_id="coffee", region="Kiambu")
    )
    second = await agro_marketplace.product_catalog.create(
        AgriculturalProduct(name="Coffee Arabica", sku="COF-1", farmer_id="f1", crop_id="coffee", region="Kiambu")
    )
    assert second.duplicate_of == first.product_id
    dupes = agro_marketplace.product_catalog.find_duplicates(second.product_id)
    assert any(d.product_id == first.product_id for d in dupes)


@pytest.mark.asyncio
async def test_warehouse_inventory_harvest_flow():
    season = agro_marketplace.harvest.create_season(Season(name="Long Rains", year=2026, region="Rift"))
    harvest = await agro_marketplace.harvest.register_harvest(
        HarvestRecord(
            farm_id="farm-1",
            crop_id="maize",
            season_id=season.season_id,
            region="Rift",
            quantity=30,
            moisture_pct=13,
            protein_pct=11,
            foreign_material_pct=1,
        )
    )
    assert harvest.harvest_id
    batch = agro_marketplace.harvest.create_batch(
        HarvestBatch(harvest_id=harvest.harvest_id, quantity=30, warehouse_id="pending")
    )
    assert batch.batch_code

    warehouse = await agro_marketplace.warehouse_engine.create_warehouse(
        AgroWarehouse(name="Central Silo", region="Rift", capacity_tons=200)
    )
    location = agro_marketplace.warehouse_engine.create_location(
        StorageLocation(warehouse_id=warehouse.warehouse_id, code="A-01", zone="dry", capacity_tons=100)
    )
    product = await agro_marketplace.product_catalog.create(
        AgriculturalProduct(name="Rift Maize", region="Rift", quantity=30, price=160)
    )
    lot = await agro_marketplace.storage.store_batch_lot(
        StorageLotRecord(
            warehouse_id=warehouse.warehouse_id,
            location_id=location.location_id,
            product_id=product.product_id,
            batch_id=batch.batch_id,
            harvest_id=harvest.harvest_id,
            quantity_tons=20,
        )
    )
    assert lot.status == "stored"

    # Reset used capacity effect from lot for clean inventory ops on same warehouse capacity budget
    wh = agro_marketplace.warehouse_engine.get_warehouse(warehouse.warehouse_id)
    assert wh.used_tons >= 20

    item = await agro_marketplace.inventory.incoming_harvest(
        product_id=product.product_id,
        warehouse_id=warehouse.warehouse_id,
        quantity=10,
        batch_id=batch.batch_id,
    )
    assert item.quantity == 10

    warehouse2 = await agro_marketplace.warehouse_engine.create_warehouse(
        AgroWarehouse(name="Port Silo", region="Mombasa", capacity_tons=300)
    )
    transfer = await agro_marketplace.inventory.transfer(
        product_id=product.product_id,
        from_warehouse_id=warehouse.warehouse_id,
        to_warehouse_id=warehouse2.warehouse_id,
        quantity=4,
    )
    assert transfer.movement_type.value == "transfer"

    shipment = await agro_marketplace.inventory.prepare_shipment(
        product_id=product.product_id,
        warehouse_id=warehouse2.warehouse_id,
        quantity=2,
        reference="truck-1",
    )
    assert shipment.movement_type.value == "outgoing"

    cert = agro_marketplace.certification.issue(
        QualityCertificateRecord(harvest_id=harvest.harvest_id, issuer="KEBS", product_id=product.product_id)
    )
    verified = await agro_marketplace.certification.verify(cert.certificate_id)
    assert verified.verified is True


@pytest.mark.asyncio
async def test_search_engines():
    await agro_marketplace.product_catalog.create(
        AgriculturalProduct(name="Green Tea", region="Kericho", quantity=5, price=90)
    )
    await agro_marketplace.harvest.register_harvest(
        HarvestRecord(crop_id="tea", region="Kericho", quantity=5, notes="premium flush")
    )
    await agro_marketplace.warehouse_engine.create_warehouse(
        AgroWarehouse(name="Tea Store", region="Kericho", capacity_tons=50)
    )
    products = agro_marketplace.search.search_products(query="Tea")
    assert products
    region = agro_marketplace.search.search_by_region("Kericho")
    assert region["products"] and region["harvests"] and region["warehouses"]
    semantic = await agro_marketplace.search.semantic_search("Tea")
    assert semantic


def test_health_sprint_82_layers():
    health = agro_marketplace.health()
    assert health["application_version"] == "1.4.0-alpha"
    assert health["catalog_layer"] == "1.0"
    assert health["warehouse_layer"] == "1.0"
    assert health["inventory_layer"] == "1.0"
    assert health["harvest_layer"] == "1.0"


@pytest.mark.asyncio
async def test_rest_catalog_and_warehouse(client: TestClient):
    resp = await client.post(
        "/api/agro/v1/catalog/products",
        json={"name": "Sorghum", "region": "Kitui", "quantity": 12, "price": 140},
    )
    assert resp.status == 201
    product = await resp.json()

    wh = await client.post(
        "/api/agro/v1/warehouse/warehouses",
        json={"name": "Kitui Depot", "region": "Kitui", "capacity_tons": 80},
    )
    assert wh.status == 201
    warehouse = await wh.json()

    incoming = await client.post(
        "/api/agro/v1/inventory/incoming",
        json={
            "product_id": product["product_id"],
            "warehouse_id": warehouse["warehouse_id"],
            "quantity": 8,
        },
    )
    assert incoming.status == 201

    search = await client.get("/api/agro/v1/search/products", params={"q": "Sorghum"})
    assert search.status == 200
    data = await search.json()
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_rest_harvest_register(client: TestClient):
    season = await client.post(
        "/api/agro/v1/harvest/seasons",
        json={"name": "Short Rains", "year": 2026, "region": "Embu"},
    )
    assert season.status == 201
    season_data = await season.json()
    harvest = await client.post(
        "/api/agro/v1/harvest/records",
        json={
            "crop_id": "beans",
            "season_id": season_data["season_id"],
            "region": "Embu",
            "quantity": 7,
            "moisture_pct": 12,
        },
    )
    assert harvest.status == 201
