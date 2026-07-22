# Auto Marketplace — Auctions, Financing, Insurance & Transactions (Sprint 10.4)

Commercial auction, loan/lease, insurance, escrow, and vehicle purchase workflows for **Auto Marketplace 2.0.0**.

| Field | Value |
|-------|-------|
| Application version | `2.0.0` |
| `transaction_engine` | `1.0` |
| `auction_engine` | `1.0` |
| `finance_engine` | `1.0` |
| `insurance_engine` | `1.0` |

**Hard constraint:** AI Platform Core, AI Ecosystem, Agro Marketplace, and Port ERP are not modified. All work lives under `applications/auto_marketplace/`.

## Domain facade

```python
from applications.auto_marketplace import auto_marketplace

assert auto_marketplace.config.transaction_engine == "1.0"
metrics = auto_marketplace.transactions.metrics()
```

## Auction Engine

English, Dutch, timed, dealer, and wholesale auctions with reserve, Buy Now, bid history, and automatic bidding.

```python
from applications.auto_marketplace.transactions.models import AdvancedAuction, AuctionType

lot = auto_marketplace.transactions.auctions.create(
    AdvancedAuction(
        vehicle_id="v1",
        auction_type=AuctionType.ENGLISH,
        start_price=10000,
        reserve_price=12000,
        buy_now_price=15000,
    )
)
auto_marketplace.transactions.auctions.start(lot.auction_id)
auto_marketplace.transactions.auctions.place_bid(lot.auction_id, "buyer-1", 11000)
auto_marketplace.transactions.auctions.register_auto_bid(lot.auction_id, "buyer-2", 14000)
```

## Financing

Loan calculator, bank rate comparison, credit offers, and approval workflow (`/api/auto/v1/finance`).

```python
calc = auto_marketplace.transactions.financing.calculate_payment(25000, 9.5, 48)
offers = auto_marketplace.transactions.financing.compare_rates(25000, 36)
loan = auto_marketplace.transactions.financing.create_offer(
    buyer_id="b1", principal=25000, annual_rate_pct=9.5, term_months=36
)
auto_marketplace.transactions.financing.approve(loan.offer_id)
```

## Leasing

Personal, business, and fleet leasing with residual value and contract generation.

```python
from applications.auto_marketplace.transactions.models import LeaseType

lease = auto_marketplace.transactions.leasing.quote(
    buyer_id="b1", vehicle_price=40000, lease_type=LeaseType.BUSINESS
)
auto_marketplace.transactions.leasing.generate_contract(lease.lease_id)
```

## Insurance

Quotations, partner comparison, risk scoring, coverage recommendations, and claims support.

```python
quote = auto_marketplace.transactions.insurance.quote(buyer_id="b1", year=2021, mileage_km=30000)
policies = auto_marketplace.transactions.insurance.compare(buyer_id="b1")
claim = auto_marketplace.transactions.insurance.open_claim(quote.quote_id, "Glass damage")
```

## Vehicle Transactions

Purchase workflow: reserve → offer / counter → digital contract → e-sign → escrow payment → ownership transfer → delivery → complete.

```python
from applications.auto_marketplace.transactions.models import VehicleTransaction

tx = auto_marketplace.transactions.transactions.create(
    VehicleTransaction(vehicle_id="v1", buyer_id="b1", seller_id="s1", price=22000)
)
auto_marketplace.transactions.transactions.reserve(tx.transaction_id, deposit=500)
auto_marketplace.transactions.transactions.make_offer(tx.transaction_id, 21000)
auto_marketplace.transactions.transactions.counter_offer(tx.transaction_id, 21500)
auto_marketplace.transactions.transactions.sign(tx.transaction_id, "b1")
auto_marketplace.transactions.transactions.fund_escrow(tx.transaction_id)
auto_marketplace.transactions.transactions.transfer_ownership(tx.transaction_id)
auto_marketplace.transactions.transactions.deliver(tx.transaction_id, location="Dealer lot")
auto_marketplace.transactions.transactions.complete(tx.transaction_id)
```

## Escrow & Payments

Secure hold/release with dispute workflow; invoices, deposits, refunds, installments, and multi-currency history via `/api/auto/v1/payments`.

## REST API

| Prefix | Capability |
|--------|------------|
| `/api/auto/v1/auctions` | Commercial auctions |
| `/api/auto/v1/finance` | Loan calculator / offers (+ legacy finance docs) |
| `/api/auto/v1/leasing` | Lease quotes & contracts |
| `/api/auto/v1/insurance` | Quotes, compare, claims |
| `/api/auto/v1/transactions` | Vehicle purchase workflow |
| `/api/auto/v1/payments` | Transaction payments |

## Modules

`auctions/` · `financing/` · `leasing/` · `insurance/` · `transactions/` · `escrow/` · `payments/` · `ownership_transfer/` · `contracts/` · `documents/`
