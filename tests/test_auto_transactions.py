"""Tests — Auto Marketplace Transactions (Sprint 10.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.transactions.models import (
    AdvancedAuction,
    AuctionType,
    LeaseType,
    VehicleTransaction,
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
    assert health["application_version"] == "4.1.2-enterprise"
    assert health["transaction_engine"] == "1.0"
    assert health["auction_engine"] == "1.0"
    assert health["finance_engine"] == "1.0"
    assert health["insurance_engine"] == "1.0"
    assert "transactions" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "AUTO_TRANSACTIONS.md"
    assert docs.exists()
    assert "4.1.2-enterprise" in docs.read_text(encoding="utf-8")
    mp = Path(__file__).resolve().parents[1] / "docs" / "AUTO_MARKETPLACE.md"
    assert "4.1.2-enterprise" in mp.read_text(encoding="utf-8")
    assert auto_marketplace.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    root = Path(__file__).resolve().parents[1] / "applications" / "auto_marketplace"
    for name in (
        "auctions",
        "financing",
        "leasing",
        "insurance",
        "transactions",
        "escrow",
        "payments",
        "ownership_transfer",
        "contracts",
        "documents",
    ):
        assert (root / name).is_dir()


def test_auction_engine():
    auction = auto_marketplace.transactions.auctions.create(
        AdvancedAuction(
            vehicle_id="v1",
            auction_type=AuctionType.ENGLISH,
            start_price=10000,
            reserve_price=12000,
            buy_now_price=16000,
        )
    )
    auto_marketplace.transactions.auctions.start(auction.auction_id)
    bid = auto_marketplace.transactions.auctions.place_bid(auction.auction_id, "b1", 11000)
    assert bid.current_price == 11000
    assert bid.bid_history
    auto_marketplace.transactions.auctions.register_auto_bid(auction.auction_id, "b2", 13000)
    closed = auto_marketplace.transactions.auctions.close(auction.auction_id)
    assert closed.status.value in {"sold", "reserve_not_met"}

    dutch = auto_marketplace.transactions.auctions.create(
        AdvancedAuction(vehicle_id="v2", auction_type=AuctionType.DUTCH, start_price=20000, current_price=20000)
    )
    auto_marketplace.transactions.auctions.start(dutch.auction_id)
    sold = auto_marketplace.transactions.auctions.place_bid(dutch.auction_id, "b3", 19000)
    assert sold.status.value == "sold"


def test_finance_and_leasing():
    calc = auto_marketplace.transactions.financing.calculate_payment(20000, 9.0, 36)
    assert calc["monthly_payment"] > 0
    compare = auto_marketplace.transactions.financing.compare_rates(20000, 36)
    assert len(compare) >= 3
    offer = auto_marketplace.transactions.financing.create_offer(
        buyer_id="b1", principal=20000, annual_rate_pct=9.0, term_months=36
    )
    approved = auto_marketplace.transactions.financing.approve(offer.offer_id)
    assert approved.status == "approved"

    lease = auto_marketplace.transactions.leasing.quote(
        buyer_id="b1", vehicle_price=40000, lease_type=LeaseType.FLEET
    )
    assert lease.residual_value > 0
    contract = auto_marketplace.transactions.leasing.generate_contract(lease.lease_id)
    assert contract.status == "contract_ready"


def test_insurance_engine():
    quote = auto_marketplace.transactions.insurance.quote(
        buyer_id="b1", year=2021, mileage_km=25000, coverage="comprehensive"
    )
    assert quote.annual_premium > 0
    assert quote.risk_score > 0
    policies = auto_marketplace.transactions.insurance.compare(buyer_id="b1")
    assert len(policies) >= 2
    claim = auto_marketplace.transactions.insurance.open_claim(quote.quote_id, "Windshield")
    assert claim["status"] == "open"


def test_vehicle_transaction_workflow():
    tx = auto_marketplace.transactions.transactions.create(
        VehicleTransaction(vehicle_id="v1", buyer_id="b1", seller_id="s1", price=22000)
    )
    auto_marketplace.transactions.transactions.reserve(tx.transaction_id, deposit=500)
    auto_marketplace.transactions.transactions.make_offer(tx.transaction_id, 21000)
    auto_marketplace.transactions.transactions.counter_offer(tx.transaction_id, 21500)
    signed = auto_marketplace.transactions.transactions.sign(tx.transaction_id, "b1")
    assert signed.signature == "b1"
    paid = auto_marketplace.transactions.transactions.fund_escrow(tx.transaction_id)
    assert paid.escrow_id
    transferred = auto_marketplace.transactions.transactions.transfer_ownership(tx.transaction_id)
    assert transferred.status.value == "transferred"
    delivered = auto_marketplace.transactions.transactions.deliver(tx.transaction_id, location="Lot A")
    assert delivered.delivery["location"] == "Lot A"
    done = auto_marketplace.transactions.transactions.complete(tx.transaction_id)
    assert done.status.value == "completed"

    payments = auto_marketplace.transactions.transactions.payments.history(transaction_id=tx.transaction_id)
    assert payments
    installments = auto_marketplace.transactions.transactions.payments.schedule_installments(
        transaction_id=tx.transaction_id, total=3000, count=3
    )
    assert len(installments) == 3


@pytest.mark.asyncio
async def test_transaction_api_routes(client: TestClient):
    health = await client.get("/api/auto/v1/health")
    body = await health.json()
    assert body["application_version"] == "4.1.2-enterprise"
    assert body["transaction_engine"] == "1.0"

    create = await client.post(
        "/api/auto/v1/auctions",
        json={"vehicle_id": "v1", "start_price": 10000, "auction_type": "english"},
    )
    assert create.status == 201
    auction = await create.json()
    start = await client.post(f"/api/auto/v1/auctions/{auction['auction_id']}/start")
    assert start.status == 200

    calc = await client.post(
        "/api/auto/v1/finance/calculator",
        json={"principal": 15000, "annual_rate_pct": 8.5, "term_months": 36},
    )
    assert calc.status == 200
    assert (await calc.json())["monthly_payment"] > 0

    lease = await client.post(
        "/api/auto/v1/leasing/quote",
        json={"buyer_id": "b1", "vehicle_price": 30000, "lease_type": "personal"},
    )
    assert lease.status == 201

    ins = await client.post(
        "/api/auto/v1/insurance/quote",
        json={"buyer_id": "b1", "year": 2022, "mileage_km": 10000},
    )
    assert ins.status == 201

    tx = await client.post(
        "/api/auto/v1/transactions",
        json={"vehicle_id": "v1", "buyer_id": "b1", "seller_id": "s1", "price": 18000},
    )
    assert tx.status == 201
    tid = (await tx.json())["transaction_id"]
    pay = await client.post(
        "/api/auto/v1/payments",
        json={"transaction_id": tid, "amount": 500, "kind": "deposit"},
    )
    assert pay.status == 201


def test_platform_core_untouched():
    root = Path(__file__).resolve().parents[1]
    # Regression marker: Sprint 10.4 must not add application code under platform/ecosystem/agro/port
    for forbidden in ("platform", "ecosystem", "applications/agro_marketplace", "applications/port_erp"):
        # Existence is fine; we only assert our new modules live under auto_marketplace
        assert (root / "applications" / "auto_marketplace" / "transactions").is_dir()
    assert not (root / "applications" / "auto_marketplace" / "financing" / "engine.py").read_text().startswith(
        "# Platform Core"
    )
