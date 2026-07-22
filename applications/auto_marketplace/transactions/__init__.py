"""Transaction domain — Sprint 10.4."""

from __future__ import annotations

from typing import Any

__all__ = [
    "TransactionDomainEngine",
    "transaction_domain_engine",
    "VehicleTransactionEngine",
    "vehicle_transaction_engine",
    "AdvancedAuction",
    "AuctionStatus",
    "AuctionType",
    "EscrowAccount",
    "InsuranceQuote",
    "LeaseOffer",
    "LeaseType",
    "LoanOffer",
    "TransactionStatus",
    "VehicleTransaction",
]


def __getattr__(name: str) -> Any:
    if name in {"TransactionDomainEngine", "transaction_domain_engine"}:
        from applications.auto_marketplace.transactions.facade import (
            TransactionDomainEngine,
            transaction_domain_engine,
        )

        return TransactionDomainEngine if name == "TransactionDomainEngine" else transaction_domain_engine
    if name in {"VehicleTransactionEngine", "vehicle_transaction_engine"}:
        from applications.auto_marketplace.transactions.engine import (
            VehicleTransactionEngine,
            vehicle_transaction_engine,
        )

        return VehicleTransactionEngine if name == "VehicleTransactionEngine" else vehicle_transaction_engine
    if name in {
        "AdvancedAuction",
        "AuctionStatus",
        "AuctionType",
        "EscrowAccount",
        "InsuranceQuote",
        "LeaseOffer",
        "LeaseType",
        "LoanOffer",
        "TransactionStatus",
        "VehicleTransaction",
    }:
        from applications.auto_marketplace.transactions import models as m

        return getattr(m, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
