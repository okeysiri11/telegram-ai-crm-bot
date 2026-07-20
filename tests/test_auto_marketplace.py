"""Tests — Auto Marketplace Foundation (Sprint 6.1)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.models import (
    Customer,
    Dealer,
    Vehicle,
    VehicleSpecification,
    VehicleStatus,
)


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


def test_catalog_service_create_and_list():
    dealer = auto_marketplace.dealers.create_dealer(Dealer(name="Test Motors"))
    vehicle = Vehicle(
        dealer_id=dealer.dealer_id,
        specification=VehicleSpecification(make="Toyota", model="Camry", year=2022, mileage_km=15000),
        price=25000,
        status=VehicleStatus.LISTED,
    )
    auto_marketplace.catalog.create_vehicle(vehicle)
    listed = auto_marketplace.catalog.list_vehicles(status=VehicleStatus.LISTED)
    assert len(listed) == 1
    assert listed[0].specification.make == "Toyota"


def test_search_service_filters():
    auto_marketplace.catalog.create_vehicle(
        Vehicle(
            specification=VehicleSpecification(make="BMW", model="X5", year=2021),
            price=60000,
            status=VehicleStatus.LISTED,
        )
    )
    results = auto_marketplace.search.search_vehicles(make="BMW")
    assert len(results) == 1


def test_crm_lead_and_deal_flow():
    customer = auto_marketplace.customers.create_customer(
        Customer(first_name="Ann", last_name="Buyer", email="ann@example.com")
    )
    from applications.auto_marketplace.shared.models import Lead

    lead = auto_marketplace.crm.create_lead(
        Lead(customer_id=customer.customer_id, vehicle_id="v1", dealer_id="d1")
    )
    assert lead.lead_id
    assert auto_marketplace.crm.list_leads()


def test_pricing_and_recommendations():
    customer = auto_marketplace.customers.create_customer(
        Customer(email="buyer@example.com", preferences={"budget_max": 30000, "make": "Honda"})
    )
    auto_marketplace.catalog.create_vehicle(
        Vehicle(
            specification=VehicleSpecification(make="Honda", model="Civic", year=2020),
            price=22000,
            status=VehicleStatus.LISTED,
        )
    )
    recs = auto_marketplace.recommendations.recommend_for_customer(customer.customer_id)
    assert recs


def test_payment_and_document_flow():
    from applications.auto_marketplace.shared.models import Payment

    payment = auto_marketplace.payments.create_payment(
        Payment(deal_id="deal-1", customer_id="cust-1", amount=1000)
    )
    captured = auto_marketplace.payments.capture_payment(payment.payment_id)
    assert captured.status.value == "captured"


@pytest.mark.asyncio
async def test_rest_health(client: TestClient):
    resp = await client.get("/api/auto/v1/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["application"] == "auto_marketplace"


@pytest.mark.asyncio
async def test_rest_create_vehicle(client: TestClient):
    resp = await client.post(
        "/api/auto/v1/vehicles",
        json={
            "dealer_id": "d1",
            "price": 35000,
            "specification": {"make": "Audi", "model": "A4", "year": 2023, "mileage_km": 5000},
        },
    )
    assert resp.status == 201
    data = await resp.json()
    assert data["specification"]["make"] == "Audi"


@pytest.mark.asyncio
async def test_rest_search(client: TestClient):
    await client.post(
        "/api/auto/v1/vehicles",
        json={
            "price": 15000,
            "specification": {"make": "Ford", "model": "Focus", "year": 2019},
        },
    )
    resp = await client.get("/api/auto/v1/search", params={"make": "Ford"})
    assert resp.status == 200
    data = await resp.json()
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_internal_requires_auth(client: TestClient):
    resp = await client.get("/internal/auto/v1/pipeline")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_internal_with_auth(client: TestClient):
    resp = await client.get(
        "/internal/auto/v1/pipeline",
        headers={"Authorization": "Bearer test-token"},
    )
    assert resp.status == 200


@pytest.mark.asyncio
async def test_platform_bridge_fallback():
    from applications.auto_marketplace.integrations.platform_bridge import platform_bridge

    result = await platform_bridge.orchestrate_vehicle_inquiry("v1", "c1")
    assert "vehicle_id" in result


def test_analytics_dashboard():
    metrics = auto_marketplace.analytics.dashboard_metrics()
    assert "vehicles" in metrics
