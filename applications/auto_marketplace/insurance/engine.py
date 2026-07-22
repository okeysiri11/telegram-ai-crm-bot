# Insurance Engine — quotations, comparison, risk, claims, partners.

from __future__ import annotations

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transactions.models import InsuranceQuote


class InsuranceEngine:
    PARTNERS = ("SafeDrive Mutual", "FleetCover", "AutoShield Partners")

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def risk_score(self, *, year: int = 2020, mileage_km: int = 50000, claims_count: int = 0) -> float:
        age = max(0, 2026 - year)
        score = 40.0 + age * 1.5 + mileage_km / 20000 + claims_count * 12
        return round(min(100.0, max(5.0, score)), 2)

    def quote(
        self,
        *,
        buyer_id: str,
        vehicle_id: str = "",
        coverage: str = "comprehensive",
        year: int = 2020,
        mileage_km: int = 50000,
        claims_count: int = 0,
        provider: str = "",
        currency: str = "USD",
    ) -> InsuranceQuote:
        if not buyer_id:
            raise ValidationError("buyer_id is required")
        risk = self.risk_score(year=year, mileage_km=mileage_km, claims_count=claims_count)
        base = 800.0 if coverage == "liability" else 1400.0 if coverage == "comprehensive" else 1100.0
        premium = round(base * (1 + risk / 200), 2)
        deductible = 500.0 if coverage == "liability" else 750.0
        provider = provider or self.PARTNERS[0]
        recs = [
            "Consider roadside assistance add-on",
            "Raise deductible to lower premium" if risk < 50 else "Keep full coverage given elevated risk",
        ]
        if claims_count:
            recs.append("Claims history may affect renewal rates")
        quote = InsuranceQuote(
            buyer_id=buyer_id,
            vehicle_id=vehicle_id,
            provider=provider,
            coverage=coverage,
            annual_premium=premium,
            deductible=deductible,
            risk_score=risk,
            currency=currency,
            recommendations=recs,
        )
        return self._store.insurance_quotes.save(quote.quote_id, quote)

    def compare(self, *, buyer_id: str, vehicle_id: str = "", year: int = 2020, mileage_km: int = 50000) -> list[dict]:
        out = []
        for i, partner in enumerate(self.PARTNERS):
            q = self.quote(
                buyer_id=buyer_id,
                vehicle_id=vehicle_id,
                year=year,
                mileage_km=mileage_km,
                provider=partner,
                coverage="comprehensive" if i == 0 else ("collision" if i == 1 else "liability"),
            )
            out.append(q.to_dict())
        return sorted(out, key=lambda x: x["annual_premium"])

    def open_claim(self, quote_id: str, description: str) -> dict:
        quote = self._store.insurance_quotes.get(quote_id)
        if quote is None:
            raise NotFoundError("InsuranceQuote", quote_id)
        claim = {
            "quote_id": quote_id,
            "provider": quote.provider,
            "description": description,
            "status": "open",
            "support": "Claims desk will contact within 24h",
        }
        return claim

    def list_quotes(self, *, buyer_id: str = "") -> list[InsuranceQuote]:
        items = self._store.insurance_quotes.list_all()
        if buyer_id:
            items = [q for q in items if q.buyer_id == buyer_id]
        return items

    def metrics(self) -> dict:
        return {"insurance_quotes": self._store.insurance_quotes.count(), "partners": list(self.PARTNERS)}


insurance_engine = InsuranceEngine()
