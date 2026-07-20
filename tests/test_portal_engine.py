"""Tests — Customer Portal, Dealer Portal & Mobile API (Sprint 6.7)."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.authentication.models import PortalRole
from applications.auto_marketplace.authentication.security import portal_security
from applications.auto_marketplace.vehicle_catalog.models import CatalogVehicle


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


def test_portal_security_roles():
    assert portal_security.authorize(PortalRole.CUSTOMER, "favorites.manage")
    assert portal_security.authorize(PortalRole.DEALER, "inventory.manage")
    assert not portal_security.authorize(PortalRole.CUSTOMER, "dealer.dashboard")


@pytest.mark.asyncio
async def test_customer_registration_and_login():
    user, token = await auto_marketplace.portal_engine.auth.register_customer(
        email="portal@test.com", password="secret123", first_name="Portal", last_name="User"
    )
    assert user.customer_id
    assert token.access_token
    logged_in, _ = await auto_marketplace.portal_engine.auth.login("portal@test.com", "secret123")
    assert logged_in.user_id == user.user_id


@pytest.mark.asyncio
async def test_favorites_and_garage():
    user, _ = await auto_marketplace.portal_engine.auth.register_customer(email="fav@test.com", password="pass")
    fav = await auto_marketplace.portal_engine.favorites.add_favorite(user.user_id, "v1")
    assert fav.vehicle_id == "v1"
    gv = auto_marketplace.portal_engine.garage.add_vehicle(user.user_id, make="Toyota", model="Camry", year=2020)
    assert gv.make == "Toyota"


@pytest.mark.asyncio
async def test_test_drive_and_offer():
    user, _ = await auto_marketplace.portal_engine.auth.register_customer(email="book@test.com", password="pass")
    auto_marketplace.store.catalog_vehicles.save(
        "v-book", CatalogVehicle(vehicle_id="v-book", brand="Honda", model="Civic", price=22000, year=2022, dealer_id="d1")
    )
    booking = await auto_marketplace.portal_engine.customer.book_test_drive(
        user.user_id, customer_id=user.customer_id, vehicle_id="v-book", dealer_id="d1", scheduled_at=9999999999
    )
    assert booking.booking_id
    offer = await auto_marketplace.portal_engine.customer.request_offer(
        user.user_id, customer_id=user.customer_id, vehicle_id="v-book", dealer_id="d1", proposed_amount=21000
    )
    assert offer.request_id


@pytest.mark.asyncio
async def test_dealer_portal():
    user, _ = await auto_marketplace.portal_engine.auth.register_dealer(
        email="dealer@test.com", password="pass", dealer_id="d1", display_name="Test Dealer"
    )
    dash = auto_marketplace.portal_engine.dealer.dashboard("d1")
    assert dash["dealer_id"] == "d1"
    sales = auto_marketplace.portal_engine.dealer.sales_tracking("d1")
    assert "total_deals" in sales


@pytest.mark.asyncio
async def test_mobile_api():
    info = auto_marketplace.portal_engine.mobile.api_info()
    assert info["api_version"] == "v1"
    allowed, remaining = auto_marketplace.portal_engine.mobile.check_rate_limit("client-1")
    assert allowed
    assert remaining > 0


@pytest.mark.asyncio
async def test_partner_api():
    conn, api_key = await auto_marketplace.portal_engine.partner.connect_partner(
        name="InsureCo", partner_type="insurance", webhook_url="https://partner.example/hook"
    )
    assert conn.partner_type == "insurance"
    validated = auto_marketplace.portal_engine.partner.validate_api_key(api_key)
    assert validated is not None
    quote = await auto_marketplace.portal_engine.partner.financing_quote(25000)
    assert quote["monthly_payment"] > 0


@pytest.mark.asyncio
async def test_public_api():
    auto_marketplace.store.catalog_vehicles.save(
        "v-pub", CatalogVehicle(vehicle_id="v-pub", brand="Ford", model="Focus", price=15000, year=2021)
    )
    items = auto_marketplace.portal_engine.public.search(query="Ford")
    assert len(items) >= 1


@pytest.mark.asyncio
async def test_portal_api(client: TestClient):
    resp = await client.post(
        "/api/auto/v1/portal/auth/register",
        json={"email": "api-portal@test.com", "password": "secret", "first_name": "Api"},
    )
    assert resp.status == 201
    data = await resp.json()
    token = data["token"]["access_token"]

    resp = await client.get("/api/auto/mobile/v1/info")
    assert resp.status == 200

    resp = await client.get("/api/auto/v1/public/stats")
    assert resp.status == 200

    resp = await client.get(
        "/api/auto/v1/portal/customer/favorites",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status == 200


@pytest.mark.asyncio
async def test_customer_registered_event():
    received: list = []
    from events import subscribe

    subscribe("CustomerRegisteredEvent", lambda e: received.append(e))
    await auto_marketplace.portal_engine.auth.register_customer(email="evt@test.com", password="pass")
    await asyncio.sleep(0.05)
    assert len(received) >= 1
