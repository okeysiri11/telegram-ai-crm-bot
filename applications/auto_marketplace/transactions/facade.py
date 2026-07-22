# Transaction domain facade — Sprint 10.4.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.auctions.commercial import CommercialAuctionEngine, commercial_auction_engine
from applications.auto_marketplace.financing.engine import FinancingEngine, financing_engine
from applications.auto_marketplace.insurance.engine import InsuranceEngine, insurance_engine
from applications.auto_marketplace.leasing.engine import LeasingEngine, leasing_engine
from applications.auto_marketplace.transactions.engine import VehicleTransactionEngine, vehicle_transaction_engine


class TransactionDomainEngine:
    """Sprint 10.4 — auctions, financing, leasing, insurance, vehicle transactions."""

    def __init__(
        self,
        auctions: CommercialAuctionEngine | None = None,
        financing: FinancingEngine | None = None,
        leasing: LeasingEngine | None = None,
        insurance: InsuranceEngine | None = None,
        transactions: VehicleTransactionEngine | None = None,
    ) -> None:
        self.auctions = auctions or commercial_auction_engine
        self.financing = financing or financing_engine
        self.leasing = leasing or leasing_engine
        self.insurance = insurance or insurance_engine
        self.transactions = transactions or vehicle_transaction_engine

    def metrics(self) -> dict[str, Any]:
        return {
            "auctions": self.auctions.metrics(),
            "financing": self.financing.metrics(),
            "leasing": self.leasing.metrics(),
            "insurance": self.insurance.metrics(),
            "transactions": self.transactions.metrics(),
        }


transaction_domain_engine = TransactionDomainEngine()
