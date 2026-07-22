# Financing Engine — loan calculator, credit offers, approval.

from __future__ import annotations

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transactions.models import LoanOffer


class FinancingEngine:
    BANKS = ("AutoBank", "Prime Credit", "Fleet Finance Co")

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def calculate_payment(self, principal: float, annual_rate_pct: float, term_months: int) -> dict:
        if principal <= 0 or term_months <= 0:
            raise ValidationError("principal and term_months must be positive")
        r = (annual_rate_pct / 100) / 12
        if r == 0:
            monthly = principal / term_months
        else:
            monthly = principal * (r * (1 + r) ** term_months) / ((1 + r) ** term_months - 1)
        total = monthly * term_months
        return {
            "principal": principal,
            "annual_rate_pct": annual_rate_pct,
            "term_months": term_months,
            "monthly_payment": round(monthly, 2),
            "total_interest": round(total - principal, 2),
            "total_payable": round(total, 2),
        }

    def compare_rates(self, principal: float, term_months: int = 36) -> list[dict]:
        offers = []
        for i, bank in enumerate(self.BANKS):
            rate = 8.5 + i * 1.25
            calc = self.calculate_payment(principal, rate, term_months)
            offers.append({"bank": bank, **calc})
        return sorted(offers, key=lambda o: o["monthly_payment"])

    def create_offer(
        self,
        *,
        buyer_id: str,
        vehicle_id: str = "",
        principal: float,
        annual_rate_pct: float,
        term_months: int = 36,
        bank: str = "AutoBank",
        currency: str = "USD",
    ) -> LoanOffer:
        calc = self.calculate_payment(principal, annual_rate_pct, term_months)
        offer = LoanOffer(
            buyer_id=buyer_id,
            vehicle_id=vehicle_id,
            principal=principal,
            annual_rate_pct=annual_rate_pct,
            term_months=term_months,
            monthly_payment=calc["monthly_payment"],
            total_interest=calc["total_interest"],
            bank=bank,
            currency=currency,
        )
        return self._store.loan_offers.save(offer.offer_id, offer)

    def approve(self, offer_id: str) -> LoanOffer:
        offer = self._store.loan_offers.get(offer_id)
        if offer is None:
            raise NotFoundError("LoanOffer", offer_id)
        offer.status = "approved"
        return self._store.loan_offers.save(offer_id, offer)

    def list_offers(self, *, buyer_id: str = "") -> list[LoanOffer]:
        items = self._store.loan_offers.list_all()
        if buyer_id:
            items = [o for o in items if o.buyer_id == buyer_id]
        return items

    def metrics(self) -> dict:
        return {"loan_offers": self._store.loan_offers.count(), "banks": list(self.BANKS)}


financing_engine = FinancingEngine()
