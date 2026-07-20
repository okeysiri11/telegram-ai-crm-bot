# Tax service.

from __future__ import annotations

from applications.auto_marketplace.finance.models import TaxRecord
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

_TAX_RATES = {"US": 0.08, "EU": 0.20, "UK": 0.20, "DEFAULT": 0.07}


class TaxService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def calculate(
        self,
        *,
        deal_id: str = "",
        taxable_amount: float,
        jurisdiction: str = "US",
        currency: str = "USD",
    ) -> TaxRecord:
        rate = _TAX_RATES.get(jurisdiction, _TAX_RATES["DEFAULT"])
        tax_amount = round(taxable_amount * rate, 2)
        record = TaxRecord(
            deal_id=deal_id,
            jurisdiction=jurisdiction,
            rate=rate,
            taxable_amount=taxable_amount,
            tax_amount=tax_amount,
            currency=currency,
        )
        return self._store.tax_records.save(record.tax_id, record)

    def list_records(self, *, deal_id: str = "") -> list[TaxRecord]:
        items = self._store.tax_records.list_all()
        if deal_id:
            items = [t for t in items if t.deal_id == deal_id]
        return items


tax_service = TaxService()
