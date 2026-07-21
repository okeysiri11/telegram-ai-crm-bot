"""Tests — Agro Marketplace Foundation (Sprint 8.1)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.register import register_agro_marketplace_routes
from applications.agro_marketplace.shared.models import (
    Buyer,
    Contract,
    Delivery,
    ExportShipment,
    Farm,
    Farmer,
    Harvest,
    MarketplaceListing,
    Order,
    Product,
    ProductCategory,
    Warehouse,
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
async def test_farmer_product_order_flow():
    farmer = await agro_marketplace.farmers.register_farmer(
        Farmer(name="Green Fields", email="green@example.com", country="KE")
    )
    farm = agro_marketplace.farmers.create_farm(
        Farm(farmer_id=farmer.farmer_id, name="North Plot", size_hectares=12.5)
    )
    assert farm.farmer_id == farmer.farmer_id

    category = agro_marketplace.catalog.create_category(ProductCategory(name="Grains"))
    product = await agro_marketplace.products.create_product(
        Product(
            name="Maize",
            category_id=category.category_id,
            farmer_id=farmer.farmer_id,
            quantity=100,
            price=180,
        )
    )
    listing = agro_marketplace.catalog.create_listing(
        MarketplaceListing(product_id=product.product_id, title="Grade A Maize")
    )
    assert listing.is_active

    buyer = agro_marketplace.buyers.create_buyer(
        Buyer(name="Mill Co", email="mill@example.com")
    )
    order = await agro_marketplace.orders.create_order(
        Order(
            buyer_id=buyer.buyer_id,
            product_id=product.product_id,
            quantity=10,
        )
    )
    assert order.total == 1800
    assert order.farmer_id == farmer.farmer_id


@pytest.mark.asyncio
async def test_harvest_warehouse_logistics_export():
    farmer = await agro_marketplace.farmers.register_farmer(
        Farmer(name="Ada", email="ada@example.com")
    )
    farm = agro_marketplace.farmers.create_farm(
        Farm(farmer_id=farmer.farmer_id, name="River Farm")
    )
    harvest = await agro_marketplace.products.add_harvest(
        Harvest(farm_id=farm.farm_id, crop_id="wheat", quantity_tons=25)
    )
    assert harvest.quantity_tons == 25

    warehouse = agro_marketplace.warehouse.create_warehouse(
        Warehouse(name="Silo 1", capacity_tons=100, owner_id=farmer.farmer_id)
    )
    assert warehouse.capacity_tons == 100

    product = await agro_marketplace.products.create_product(
        Product(name="Wheat", farmer_id=farmer.farmer_id, price=200, quantity=25)
    )
    buyer = agro_marketplace.buyers.create_buyer(Buyer(name="Buyer", email="b@example.com"))
    order = await agro_marketplace.orders.create_order(
        Order(buyer_id=buyer.buyer_id, product_id=product.product_id, quantity=5)
    )
    delivery = await agro_marketplace.logistics.create_delivery(
        Delivery(order_id=order.order_id, carrier="AgroHaul", destination="Nairobi")
    )
    completed = await agro_marketplace.logistics.complete_delivery(delivery.delivery_id)
    assert completed.status.value == "delivered"

    shipment = await agro_marketplace.export.create_shipment(
        ExportShipment(
            order_id=order.order_id,
            exporter_id="exp-1",
            destination_country="NL",
        )
    )
    started = await agro_marketplace.export.start_export(shipment.shipment_id)
    assert started.status.value == "started"

    contract = agro_marketplace.orders.create_contract(
        Contract(order_id=order.order_id, parties=[farmer.farmer_id, buyer.buyer_id])
    )
    signed = await agro_marketplace.orders.sign_contract(contract.contract_id)
    assert signed.status.value == "signed"


def test_pricing_and_permissions():
    from applications.agro_marketplace.shared.models import AgroRole

    assert agro_marketplace.permissions.has_permission(AgroRole.FARMER, "products:write")
    assert agro_marketplace.permissions.has_permission(AgroRole.OWNER, "export:write")
    assert not agro_marketplace.permissions.has_permission(AgroRole.BUYER, "export:write")

    quote = agro_marketplace.pricing.quote("missing", 1)
    assert "error" in quote


def test_health_manifest_values():
    health = agro_marketplace.health()
    assert health["application"] == "agro_marketplace"
    assert health["application_version"] == "1.5.0-alpha"
    assert health["platform_dependency"] == "AI Platform Core v3.0"
    assert health["ecosystem_dependency"] == "AI Ecosystem v1.5"


@pytest.mark.asyncio
async def test_rest_health(client: TestClient):
    resp = await client.get("/api/agro/v1/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["application_name"] == "Agro Marketplace"


@pytest.mark.asyncio
async def test_rest_register_farmer_and_product(client: TestClient):
    farmer_resp = await client.post(
        "/api/agro/v1/farmers",
        json={"name": "Sam Farmer", "email": "sam@example.com", "country": "UG"},
    )
    assert farmer_resp.status == 201
    farmer = await farmer_resp.json()

    product_resp = await client.post(
        "/api/agro/v1/products",
        json={
            "name": "Coffee",
            "farmer_id": farmer["farmer_id"],
            "price": 450,
            "quantity": 8,
        },
    )
    assert product_resp.status == 201
    product = await product_resp.json()
    assert product["name"] == "Coffee"


@pytest.mark.asyncio
async def test_rest_catalog_search(client: TestClient):
    farmer_resp = await client.post(
        "/api/agro/v1/farmers",
        json={"name": "Tea Grower", "email": "tea@example.com"},
    )
    farmer = await farmer_resp.json()
    product_resp = await client.post(
        "/api/agro/v1/products",
        json={"name": "Green Tea", "farmer_id": farmer["farmer_id"], "price": 90, "quantity": 3},
    )
    product = await product_resp.json()
    await client.post(
        "/api/agro/v1/listings",
        json={"product_id": product["product_id"], "title": "Fresh Green Tea"},
    )
    resp = await client.get("/api/agro/v1/catalog/search", params={"q": "Tea"})
    assert resp.status == 200
    data = await resp.json()
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_internal_requires_auth(client: TestClient):
    resp = await client.get("/internal/agro/v1/pipeline")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_webhook_order(client: TestClient):
    resp = await client.post(
        "/webhooks/agro/v1/orders",
        json={"event": "order.created", "order_id": "o1"},
    )
    assert resp.status == 200
    data = await resp.json()
    assert data["received"] is True
