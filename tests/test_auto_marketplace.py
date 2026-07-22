"""Tests — Auto Marketplace Foundation (Sprint 10.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.foundation.models import (
    Appointment,
    Buyer,
    BuyerRequest,
    CatalogCategory,
    InspectionReport,
    Negotiation,
    VehicleBrand,
    VehicleModel,
)
from applications.auto_marketplace.shared.models import (
    Customer,
    Dealer,
    Lead,
    Reservation,
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


def test_version_modules_docs_bridges():
    health = auto_marketplace.health()
    assert health["application_name"] == "Auto Marketplace Enterprise Platform"
    assert health["application_version"] == "4.1.1-enterprise"
    assert health["platform_dependency"] == "AI Platform Core v3"
    assert health["ecosystem_dependency"] == "AI Ecosystem v1.5"
    assert "foundation" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "AUTO_MARKETPLACE.md"
    assert docs.exists()
    assert "4.1.1-enterprise" in docs.read_text(encoding="utf-8")
    assert auto_marketplace.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    assert auto_marketplace.ecosystem.ecosystem_health()["ecosystem_dependency"] == "AI Ecosystem v1.5"
    root = Path(__file__).resolve().parents[1] / "applications" / "auto_marketplace"
    for name in (
        "catalog",
        "vehicles",
        "dealers",
        "buyers",
        "crm",
        "search",
        "favorites",
        "garage",
        "inspection",
        "pricing",
        "documents",
        "shared",
    ):
        assert (root / name).is_dir()


def test_catalog_categories_and_vehicles():
    dealer = auto_marketplace.dealers.create_dealer(Dealer(name="City Motors"))
    brand = auto_marketplace.vehicles.register_brand(VehicleBrand(name="Toyota", country="JP"))
    model = auto_marketplace.vehicles.register_model(
        VehicleModel(brand_id=brand.brand_id, name="Camry", category=CatalogCategory.CARS)
    )
    assert model.category == CatalogCategory.CARS
    assert "cars" in auto_marketplace.catalog.categories()
    assert "electric_vehicles" in auto_marketplace.catalog.categories()

    vehicle = auto_marketplace.catalog.create_vehicle(
        Vehicle(
            dealer_id=dealer.dealer_id,
            specification=VehicleSpecification(
                make="Toyota",
                model="Camry",
                year=2022,
                mileage_km=12000,
                fuel_type="hybrid",
                transmission="automatic",
                body_type="sedan",
                vin="JTDBR32E720123456",
            ),
            price=25000,
            status=VehicleStatus.LISTED,
            description="Certified hybrid sedan",
        ),
        category=CatalogCategory.HYBRID.value,
    )
    assert auto_marketplace.catalog.overview()["by_category"]["hybrid_vehicles"] == 1
    vin = auto_marketplace.vehicles.parse_vin(vehicle.specification.vin)
    assert vin.valid is True


def test_search_foundation_filters():
    dealer = auto_marketplace.dealers.create_dealer(Dealer(name="Nairobi Dealer"))
    auto_marketplace.catalog.create_vehicle(
        Vehicle(
            dealer_id=dealer.dealer_id,
            specification=VehicleSpecification(
                make="BMW",
                model="X5",
                year=2021,
                mileage_km=30000,
                fuel_type="diesel",
                transmission="automatic",
                body_type="suv",
                vin="WBAXXXXXXXXXXXXX1",
            ),
            price=60000,
            status=VehicleStatus.LISTED,
            description="Nairobi region SUV",
        ),
        category=CatalogCategory.CARS.value,
    )
    results = auto_marketplace.search.search_vehicles(
        brand="BMW",
        year=2021,
        fuel="diesel",
        transmission="automatic",
        body="suv",
        max_price=65000,
        mileage_max=40000,
        region="Nairobi",
    )
    assert len(results) == 1
    assert set(auto_marketplace.search.filter_keys()) >= {
        "brand",
        "model",
        "year",
        "mileage",
        "fuel",
        "transmission",
        "body",
        "region",
        "price",
        "vin",
        "condition",
    }


def test_crm_requests_appointments_negotiations_reservations():
    buyer = auto_marketplace.buyers.register(
        Buyer(first_name="Ann", last_name="Buyer", email="ann@example.com", region="KE")
    )
    dealer = auto_marketplace.dealers.create_dealer(Dealer(name="Prime Auto"))
    vehicle = auto_marketplace.catalog.create_vehicle(
        Vehicle(
            dealer_id=dealer.dealer_id,
            specification=VehicleSpecification(make="Honda", model="Civic", year=2020),
            price=18000,
            status=VehicleStatus.LISTED,
        )
    )
    lead = auto_marketplace.crm.create_lead(
        Lead(customer_id=buyer.buyer_id, vehicle_id=vehicle.vehicle_id, dealer_id=dealer.dealer_id)
    )
    assert lead.lead_id
    req = auto_marketplace.crm.create_request(
        BuyerRequest(buyer_id=buyer.buyer_id, vehicle_id=vehicle.vehicle_id, message="Need test drive")
    )
    appt = auto_marketplace.crm.schedule_appointment(
        Appointment(
            buyer_id=buyer.buyer_id,
            dealer_id=dealer.dealer_id,
            vehicle_id=vehicle.vehicle_id,
            scheduled_at=1_700_000_000,
        )
    )
    nego = auto_marketplace.crm.start_negotiation(
        Negotiation(
            buyer_id=buyer.buyer_id,
            dealer_id=dealer.dealer_id,
            vehicle_id=vehicle.vehicle_id,
            offer_price=17000,
        )
    )
    auto_marketplace.crm.counter_negotiation(nego.negotiation_id, 17500)
    reservation = auto_marketplace.crm.reserve_vehicle(
        Reservation(
            vehicle_id=vehicle.vehicle_id,
            customer_id=buyer.buyer_id,
            dealer_id=dealer.dealer_id,
            deposit_amount=500,
        )
    )
    history = auto_marketplace.crm.customer_history(buyer.buyer_id)
    assert history["requests"] and history["appointments"] and history["negotiations"]
    assert history["reservations"][0]["reservation_id"] == reservation.reservation_id
    assert appt.appointment_id and req.request_id


def test_inspection_and_price_history():
    vehicle = auto_marketplace.catalog.create_vehicle(
        Vehicle(
            specification=VehicleSpecification(make="Ford", model="Ranger", year=2019),
            price=22000,
            status=VehicleStatus.LISTED,
        )
    )
    report = auto_marketplace.inspection.create_report(
        InspectionReport(vehicle_id=vehicle.vehicle_id, inspector="tech-1", score=88, findings=["ok"])
    )
    assert report.passed is True
    entry = auto_marketplace.pricing.record_price(vehicle.vehicle_id, 21000, reason="promo")
    assert entry["price"] == 21000
    assert len(auto_marketplace.pricing.price_history(vehicle.vehicle_id)) == 1


@pytest.mark.asyncio
async def test_rest_foundation_endpoints(client: TestClient):
    health = await client.get("/api/auto/v1/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "4.1.1-enterprise"

    catalog = await client.get("/api/auto/v1/catalog")
    assert catalog.status == 200
    catalog_body = await catalog.json()
    assert "cars" in catalog_body["categories"]

    dealer = await client.post("/api/auto/v1/dealers", json={"name": "API Motors"})
    assert dealer.status == 201
    dealer_body = await dealer.json()

    vehicle = await client.post(
        "/api/auto/v1/vehicles",
        json={
            "dealer_id": dealer_body["dealer_id"],
            "category": "cars",
            "price": 15000,
            "specification": {
                "make": "Kia",
                "model": "Sportage",
                "year": 2018,
                "fuel_type": "petrol",
                "transmission": "manual",
                "body_type": "suv",
                "vin": "KNAXXXXXXXXXXXXX1",
            },
        },
    )
    assert vehicle.status == 201

    search = await client.get("/api/auto/v1/search?brand=Kia&body=suv&fuel=petrol")
    assert search.status == 200
    search_body = await search.json()
    assert search_body["items"]

    buyer = await client.post(
        "/api/auto/v1/buyers",
        json={"first_name": "Sam", "email": "sam@example.com", "region": "KE"},
    )
    assert buyer.status == 201
    buyer_body = await buyer.json()

    crm = await client.get("/api/auto/v1/crm")
    assert crm.status == 200
    crm_body = await crm.json()
    assert crm_body["crm_foundation"] == "1.0"

    req = await client.post(
        "/api/auto/v1/crm/requests",
        json={"buyer_id": buyer_body["buyer_id"], "message": "Interested"},
    )
    assert req.status == 201


def test_legacy_foundation_flows_still_work():
    customer = auto_marketplace.customers.create_customer(
        Customer(first_name="Ann", last_name="Buyer", email="ann2@example.com")
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


def test_platform_core_and_siblings_untouched():
    root = Path(__file__).resolve().parents[1]
    assert (root / "applications" / "auto_marketplace" / "vehicles").is_dir()
    assert not (root / "ecosystem" / "auto_marketplace").exists()
