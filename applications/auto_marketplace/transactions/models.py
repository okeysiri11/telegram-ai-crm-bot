# Sprint 10.4 — auctions, financing, insurance, transactions models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class AuctionType(str, enum.Enum):
    ENGLISH = "english"
    DUTCH = "dutch"
    TIMED = "timed"
    DEALER = "dealer"
    WHOLESALE = "wholesale"


class AuctionStatus(str, enum.Enum):
    DRAFT = "draft"
    LIVE = "live"
    RESERVE_NOT_MET = "reserve_not_met"
    SOLD = "sold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TransactionStatus(str, enum.Enum):
    DRAFT = "draft"
    RESERVED = "reserved"
    OFFERED = "offered"
    COUNTERED = "countered"
    CONTRACTED = "contracted"
    SIGNED = "signed"
    PAID = "paid"
    TRANSFERRED = "transferred"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class EscrowStatus(str, enum.Enum):
    OPEN = "open"
    HOLDING = "holding"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class LeaseType(str, enum.Enum):
    PERSONAL = "personal"
    BUSINESS = "business"
    FLEET = "fleet"


@dataclass
class AdvancedAuction:
    auction_id: str = field(default_factory=_id)
    listing_id: str = ""
    vehicle_id: str = ""
    auction_type: AuctionType = AuctionType.ENGLISH
    start_price: float = 0.0
    current_price: float = 0.0
    reserve_price: float = 0.0
    buy_now_price: float | None = None
    currency: str = "USD"
    status: AuctionStatus = AuctionStatus.DRAFT
    ends_at: float = 0.0
    dealer_id: str = ""
    auto_bids: list[dict[str, Any]] = field(default_factory=list)
    bid_history: list[dict[str, Any]] = field(default_factory=list)
    winner_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "auction_id": self.auction_id,
            "listing_id": self.listing_id,
            "vehicle_id": self.vehicle_id,
            "auction_type": self.auction_type.value,
            "start_price": self.start_price,
            "current_price": self.current_price,
            "reserve_price": self.reserve_price,
            "buy_now_price": self.buy_now_price,
            "currency": self.currency,
            "status": self.status.value,
            "ends_at": self.ends_at,
            "dealer_id": self.dealer_id,
            "auto_bids": list(self.auto_bids),
            "bid_history": list(self.bid_history),
            "winner_id": self.winner_id,
            "created_at": self.created_at,
        }


@dataclass
class LoanOffer:
    offer_id: str = field(default_factory=_id)
    buyer_id: str = ""
    vehicle_id: str = ""
    principal: float = 0.0
    annual_rate_pct: float = 0.0
    term_months: int = 36
    monthly_payment: float = 0.0
    total_interest: float = 0.0
    bank: str = ""
    status: str = "quoted"
    currency: str = "USD"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "buyer_id": self.buyer_id,
            "vehicle_id": self.vehicle_id,
            "principal": self.principal,
            "annual_rate_pct": self.annual_rate_pct,
            "term_months": self.term_months,
            "monthly_payment": self.monthly_payment,
            "total_interest": self.total_interest,
            "bank": self.bank,
            "status": self.status,
            "currency": self.currency,
            "created_at": self.created_at,
        }


@dataclass
class LeaseOffer:
    lease_id: str = field(default_factory=_id)
    buyer_id: str = ""
    vehicle_id: str = ""
    lease_type: LeaseType = LeaseType.PERSONAL
    vehicle_price: float = 0.0
    residual_value: float = 0.0
    term_months: int = 36
    monthly_payment: float = 0.0
    mileage_limit_km: int = 15000
    currency: str = "USD"
    contract_text: str = ""
    status: str = "quoted"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "buyer_id": self.buyer_id,
            "vehicle_id": self.vehicle_id,
            "lease_type": self.lease_type.value,
            "vehicle_price": self.vehicle_price,
            "residual_value": self.residual_value,
            "term_months": self.term_months,
            "monthly_payment": self.monthly_payment,
            "mileage_limit_km": self.mileage_limit_km,
            "currency": self.currency,
            "contract_text": self.contract_text,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class InsuranceQuote:
    quote_id: str = field(default_factory=_id)
    buyer_id: str = ""
    vehicle_id: str = ""
    provider: str = ""
    coverage: str = "comprehensive"
    annual_premium: float = 0.0
    deductible: float = 0.0
    risk_score: float = 0.0
    currency: str = "USD"
    recommendations: list[str] = field(default_factory=list)
    status: str = "quoted"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "quote_id": self.quote_id,
            "buyer_id": self.buyer_id,
            "vehicle_id": self.vehicle_id,
            "provider": self.provider,
            "coverage": self.coverage,
            "annual_premium": self.annual_premium,
            "deductible": self.deductible,
            "risk_score": self.risk_score,
            "currency": self.currency,
            "recommendations": list(self.recommendations),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class VehicleTransaction:
    transaction_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    buyer_id: str = ""
    seller_id: str = ""
    dealer_id: str = ""
    price: float = 0.0
    currency: str = "USD"
    status: TransactionStatus = TransactionStatus.DRAFT
    offers: list[dict[str, Any]] = field(default_factory=list)
    contract_id: str = ""
    escrow_id: str = ""
    signature: str = ""
    delivery: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "vehicle_id": self.vehicle_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "dealer_id": self.dealer_id,
            "price": self.price,
            "currency": self.currency,
            "status": self.status.value,
            "offers": list(self.offers),
            "contract_id": self.contract_id,
            "escrow_id": self.escrow_id,
            "signature": self.signature,
            "delivery": dict(self.delivery),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class EscrowAccount:
    escrow_id: str = field(default_factory=_id)
    transaction_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: EscrowStatus = EscrowStatus.OPEN
    release_conditions: list[str] = field(default_factory=list)
    disputes: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "escrow_id": self.escrow_id,
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "release_conditions": list(self.release_conditions),
            "disputes": list(self.disputes),
            "created_at": self.created_at,
        }


@dataclass
class TransactionPayment:
    payment_id: str = field(default_factory=_id)
    transaction_id: str = ""
    kind: str = "invoice"  # invoice, deposit, refund, installment
    amount: float = 0.0
    currency: str = "USD"
    status: str = "pending"
    installment_no: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "transaction_id": self.transaction_id,
            "kind": self.kind,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "installment_no": self.installment_no,
            "history": list(self.history),
            "created_at": self.created_at,
        }


@dataclass
class OwnershipTransferRecord:
    transfer_id: str = field(default_factory=_id)
    transaction_id: str = ""
    vehicle_id: str = ""
    from_owner: str = ""
    to_owner: str = ""
    status: str = "pending"
    completed_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "transaction_id": self.transaction_id,
            "vehicle_id": self.vehicle_id,
            "from_owner": self.from_owner,
            "to_owner": self.to_owner,
            "status": self.status,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
        }


@dataclass
class TransactionContract:
    contract_id: str = field(default_factory=_id)
    transaction_id: str = ""
    title: str = ""
    body: str = ""
    signed: bool = False
    signed_by: str = ""
    signed_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "transaction_id": self.transaction_id,
            "title": self.title,
            "body": self.body,
            "signed": self.signed,
            "signed_by": self.signed_by,
            "signed_at": self.signed_at,
            "created_at": self.created_at,
        }
