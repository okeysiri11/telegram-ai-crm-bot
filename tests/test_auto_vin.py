"""Tests — Auto Marketplace VIN, Marketplace & Dealer Network (Sprint 10.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.marketplace.models import (
    AuctionLot,
    DealerNetworkProfile,
    MarketplaceChannel,
    MarketplaceListing,
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
    assert health["application_version"] == "1.2.0-alpha"
    assert health["vin_engine"] == "1.0"
    assert health["dealer_engine"] == "1.0"
    assert "marketplace" in health
    docs_root = Path(__file__).resolve().parents[1] / "docs"
    assert (docs_root / "AUTO_VIN.md").exists()
    assert "1.2.0-alpha" in (docs_root / "AUTO_MARKETPLACE.md").read_text(encoding="utf-8")
    assert auto_marketplace.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    assert auto_marketplace.ecosystem.ecosystem_health()["ecosystem_dependency"] == "AI Ecosystem v1.5"
    root = Path(__file__).resolve().parents[1] / "applications" / "auto_marketplace"
    for name in (
        "marketplace",
        "vin",
        "history",
        "dealer_network",
        "auctions",
        "listings",
        "media",
        "verification",
        "ownership",
        "valuation",
    ):
        assert (root / name).is_dir()


def test_marketplace_listings_and_auctions():
    listing = auto_marketplace.marketplace.create_listing(
        MarketplaceListing(
            title="2022 Toyota Camry",
            channel=MarketplaceChannel.RETAIL,
            price=25000,
            vin="JTDBR32E720123456",
            region="KE",
        )
    )
    published = auto_marketplace.marketplace.publish_listing(listing.listing_id)
    assert published.status.value == "active"
    assert "retail" in auto_marketplace.marketplace.marketplace.channels()
    browse = auto_marketplace.marketplace.marketplace.browse(channel="retail", region="KE")
    assert len(browse) == 1

    lot = auto_marketplace.marketplace.auctions.create(
        AuctionLot(listing_id=listing.listing_id, start_price=20000, reserve_price=22000)
    )
    bid = auto_marketplace.marketplace.auctions.place_bid(lot.auction_id, "buyer-1", 21000)
    assert bid.current_bid == 21000


def test_vin_intelligence():
    decoded = auto_marketplace.marketplace.vin.decode("JTDBR32E720123456")
    assert decoded.valid is True
    assert decoded.country
    assert decoded.engine
    assert decoded.factory_configuration
    assert decoded.oem_specifications
    assert decoded.recalls
    assert decoded.service_campaigns
    invalid = auto_marketplace.marketplace.vin.decode("BAD")
    assert invalid.valid is False


def test_vehicle_history_and_ownership():
    vin = "WBAXXXXXXXXXXXXX1"
    auto_marketplace.marketplace.history.add_ownership(vin, "Owner A")
    auto_marketplace.marketplace.history.add_registration(vin, "Nairobi", plate="KAA123A")
    auto_marketplace.marketplace.history.add_mileage(vin, 45000)
    auto_marketplace.marketplace.history.add_claim(vin, 1200, description="glass")
    auto_marketplace.marketplace.history.add_accident(vin, "minor")
    auto_marketplace.marketplace.history.add_repair(vin, "bumper", cost=400)
    auto_marketplace.marketplace.history.add_service(vin, "oil change", mileage_km=45000)
    auto_marketplace.marketplace.history.add_import_export(vin, "import", "JP")
    auto_marketplace.marketplace.history.set_theft_status(vin, "clear")
    auto_marketplace.marketplace.history.set_lien_status(vin, "clear")
    auto_marketplace.marketplace.history.add_inspection(vin, 90, findings=["ok"])
    summary = auto_marketplace.marketplace.history.summary(vin)
    assert summary["owners"] == 1
    assert summary["latest_mileage"] == 45000
    transfer = auto_marketplace.marketplace.ownership.transfer(
        __import__(
            "applications.auto_marketplace.marketplace.models", fromlist=["OwnershipTransfer"]
        ).OwnershipTransfer(vin=vin, from_owner="Owner A", to_owner="Owner B")
    )
    assert transfer.to_owner == "Owner B"


def test_dealer_network_and_verification_pricing():
    profile = auto_marketplace.marketplace.dealers.register_profile(
        DealerNetworkProfile(dealer_id="d1", name="Prime Motors", region="KE")
    )
    verified = auto_marketplace.marketplace.dealers.verify("d1")
    assert verified.verified is True
    rated = auto_marketplace.marketplace.dealers.rate("d1", 4.5)
    assert rated.rating == 4.5
    auto_marketplace.marketplace.dealers.add_branch("d1", {"name": "Westlands", "city": "Nairobi"})
    auto_marketplace.marketplace.dealers.add_manager("d1", {"name": "Alex", "role": "sales"})
    listing = auto_marketplace.marketplace.create_listing(
        MarketplaceListing(
            title="SUV",
            dealer_id="d1",
            channel=MarketplaceChannel.DEALER,
            price=30000,
            vin="JTDBR32E720123456",
        )
    )
    auto_marketplace.marketplace.publish_listing(listing.listing_id)
    analytics = auto_marketplace.marketplace.dealers.analytics("d1")
    assert analytics["inventory_active"] == 1
    assignment = auto_marketplace.marketplace.dealers.assign_lead("d1", "lead-1", manager_id="m1")
    assert assignment["lead_id"] == "lead-1"

    report = auto_marketplace.marketplace.verification.verify_listing(
        listing_id=listing.listing_id,
        vin="JTDBR32E720123456",
        photo_count=5,
        media_urls=["a", "b", "c"],
    )
    assert report.vin_status.value == "passed"
    valuation = auto_marketplace.marketplace.valuation.value_vehicle(
        vehicle_id="v1", vin="JTDBR32E720123456", year=2020, mileage_km=40000, base_price=20000
    )
    assert valuation.retail_price >= valuation.wholesale_price
    assert valuation.ai_valuation > 0
    assert profile.profile_id


@pytest.mark.asyncio
async def test_rest_marketplace_vin_history_dealers(client: TestClient):
    health = await client.get("/api/auto/v1/marketplace")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "1.2.0-alpha"

    listing = await client.post(
        "/api/auto/v1/marketplace/listings",
        json={
            "title": "EV Hatch",
            "channel": "electric_vehicles",
            "price": 28000,
            "vin": "JTDBR32E720123456",
            "region": "KE",
        },
    )
    assert listing.status == 201
    listing_body = await listing.json()
    pub = await client.post(f"/api/auto/v1/marketplace/listings/{listing_body['listing_id']}/publish")
    assert pub.status == 200

    vin = await client.post("/api/auto/v1/vin/decode", json={"vin": "JTDBR32E720123456"})
    assert vin.status == 200
    vin_body = await vin.json()
    assert vin_body["valid"] is True

    hist = await client.post(
        "/api/auto/v1/history/JTDBR32E720123456/events",
        json={"event": "mileage", "mileage_km": 12000},
    )
    assert hist.status == 201

    dealer = await client.post(
        "/api/auto/v1/dealers/network",
        json={"name": "Network Dealer", "region": "KE"},
    )
    assert dealer.status == 201
    dealer_body = await dealer.json()
    verify = await client.post(
        f"/api/auto/v1/dealers/{dealer_body['dealer_id']}/verify",
        json={"tier": "official"},
    )
    assert verify.status == 200

    verification = await client.post(
        "/api/auto/v1/verification",
        json={"vin": "JTDBR32E720123456", "photo_count": 4, "listing_id": listing_body["listing_id"]},
    )
    assert verification.status == 201

    pricing = await client.post(
        "/api/auto/v1/pricing/value",
        json={"vin": "JTDBR32E720123456", "year": 2021, "mileage_km": 20000, "base_price": 26000},
    )
    assert pricing.status == 201


def test_platform_core_untouched():
    root = Path(__file__).resolve().parents[1]
    assert (root / "applications" / "auto_marketplace" / "vin").is_dir()
    assert not (root / "ecosystem" / "auto_marketplace").exists()
