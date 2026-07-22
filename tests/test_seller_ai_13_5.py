"""Tests — Seller AI, Auctions & Global Network (Sprint 13.5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/seller-ai/v1"
BA = "/api/buyer-ai/v1"
DC = "/api/dealer-crm/v1"
IA = "/api/inspection-ai/v1"


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


def test_version_seller_ai_ready():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.1.5-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.1.4-enterprise"
    assert health["seller_ai_ready"] is True
    assert health["auction_platform_ready"] is True
    assert health["global_automotive_network_ready"] is True
    assert health["enterprise_automotive_marketplace_ready"] is True


def test_seller_listing_and_pricing():
    suite = auto_marketplace.seller_ai
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    seller = suite.seller.create_seller(name="Private Seller", seller_type="private")
    listing = suite.seller.create_listing(
        seller_id=seller["seller_id"],
        vin="1HGCM82633A000001",
        make="Honda",
        model="Accord",
        year=2019,
        ask_price=17000,
        photos=["a.jpg"],
    )
    copy = suite.seller.generate_listing_copy(listing["listing_id"])
    assert copy["photo_quality"] < 0.7
    pos = suite.seller.analyze_market_position(listing_id=listing["listing_id"], market_avg=17500, demand_index=0.8)
    assert pos["sale_probability"] > 0
    quote = suite.pricing.quote(vin=listing["vin"], make="Honda", model="Accord", mileage=40000, base_market=17000)
    assert quote["wholesale_price"] < quote["retail_price"]
    assert quote["future_price_prediction"] > 0


def test_auctions_and_marketplace():
    suite = auto_marketplace.seller_ai
    seller = suite.seller.create_seller(name="Auction House", seller_type="auction_house")
    listing = suite.seller.create_listing(
        seller_id=seller["seller_id"],
        vin="WBA3A5C50EF000001",
        make="BMW",
        model="320i",
        ask_price=21000,
        photos=["1.jpg", "2.jpg", "3.jpg"],
    )
    auction = suite.auctions.create_auction(listing_id=listing["listing_id"], mode="live", reserve_price=19000, start_price=18000)
    suite.auctions.place_bid(auction_id=auction["auction_id"], bidder_id="b1", amount=18500, proxy_max=20000)
    suite.auctions.place_bid(auction_id=auction["auction_id"], bidder_id="b2", amount=19500)
    closed = suite.auctions.close_auction(auction["auction_id"])
    assert closed["status"] == "sold"
    assert suite.auctions.analytics(auction["auction_id"])["bid_count"] >= 2
    with pytest.raises(ValidationError):
        suite.auctions.create_auction(listing_id=listing["listing_id"], mode="sealed")


def test_global_network_matching_bi():
    suite = auto_marketplace.seller_ai
    suite.network.register_dealer(name="Dubai Motors", country="AE", role="importer")
    trade = suite.network.publish_trade_listing(
        direction="import",
        vin="JN1TBNT31U0000001",
        origin_country="JP",
        destination_country="AE",
        price=16000,
    )
    assert trade["customs_support"] is True
    suite.network.add_shipping_route(origin="JP", destination="AE")
    regs = suite.network.country_regulations("AE")
    assert regs["compliance_checklist"]
    match = suite.matching.match(buyer_region="AE", make="Nissan", budget=20000)
    assert match["match_id"]
    for rt in ("market", "country", "brand", "dealer", "auction", "revenue"):
        assert suite.bi.report(report_type=rt)["report_type"] == rt
    for dtype in ("marketplace", "auction", "global_sales", "international_trade"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_seller_ai(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.1.5-enterprise"
    assert body["seller_ai_ready"] is True

    assert (await client.get(f"{BA}/health")).status == 200
    assert (await client.get(f"{DC}/health")).status == 200
    assert (await client.get(f"{IA}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    seller = await client.post(f"{PREFIX}/seller", json={"name": "API Seller", "seller_type": "exporter"})
    assert seller.status == 201

    pricing = await client.post(
        f"{PREFIX}/pricing",
        json={"vin": "WVWZZZ1JZXW000001", "make": "Volkswagen", "model": "Golf", "mileage": 45000},
    )
    assert pricing.status == 201

    auction = await client.get(f"{PREFIX}/auctions?auction_id={boot_body['auction_id']}")
    assert auction.status == 200

    network = await client.post(
        f"{PREFIX}/network",
        json={"action": "trade", "direction": "export", "vin": "1HGCM82633A000001", "origin_country": "US", "destination_country": "DE", "price": 15000},
    )
    assert network.status == 201

    matching = await client.post(f"{PREFIX}/matching", json={"buyer_region": "DE", "make": "Honda", "budget": 20000})
    assert matching.status == 201

    bi = await client.get(f"{PREFIX}/bi?type=revenue")
    assert bi.status == 200

    dash = await client.get(f"{PREFIX}/dashboard?type=international_trade")
    assert dash.status == 200


def test_docs_and_regression_13_5():
    for name in ("SELLER_AI.md", "AUCTION_PLATFORM.md", "GLOBAL_AUTOMOTIVE_NETWORK.md", "AI_PRICING.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "SELLER_AI.md").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "seller_ai" / "facade.py").exists()
    for pkg in ("buyer_ai", "dealer_crm", "inspection_ai", "vin_intelligence", "enterprise_automotive"):
        assert (ROOT / "applications" / "auto_marketplace" / pkg / "facade.py").exists()
    manifest = (ROOT / "applications" / "auto_marketplace" / "manifest.json").read_text()
    assert "4.1.5-enterprise" in manifest
    assert "13.5" in manifest

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
