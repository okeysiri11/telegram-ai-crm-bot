# Billing service — commission calculation and billing cycles.

from __future__ import annotations

from applications.auto_marketplace.finance.models import Commission
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class BillingService:
    DEFAULT_COMMISSION_RATE = 0.05

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def calculate_commission(
        self,
        *,
        deal_id: str,
        agent_id: str,
        dealer_id: str,
        sale_amount: float,
        rate: float | None = None,
        currency: str = "USD",
    ) -> Commission:
        effective_rate = rate if rate is not None else self.DEFAULT_COMMISSION_RATE
        commission = Commission(
            deal_id=deal_id,
            agent_id=agent_id,
            dealer_id=dealer_id,
            sale_amount=sale_amount,
            rate=effective_rate,
            amount=round(sale_amount * effective_rate, 2),
            currency=currency,
        )
        return self._store.commissions.save(commission.commission_id, commission)

    def list_commissions(self, *, dealer_id: str = "", agent_id: str = "") -> list[Commission]:
        items = self._store.commissions.list_all()
        if dealer_id:
            items = [c for c in items if c.dealer_id == dealer_id]
        if agent_id:
            items = [c for c in items if c.agent_id == agent_id]
        return items

    def dealer_billing_summary(self, dealer_id: str) -> dict:
        commissions = self.list_commissions(dealer_id=dealer_id)
        total = sum(c.amount for c in commissions)
        return {"dealer_id": dealer_id, "commission_total": round(total, 2), "count": len(commissions)}


billing_service = BillingService()
