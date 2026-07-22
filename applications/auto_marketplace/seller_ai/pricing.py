"""AI pricing engine — Sprint 13.5."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIPricing:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def quote(
        self,
        *,
        vin: str = "",
        make: str = "",
        model: str = "",
        year: int | None = None,
        mileage: int = 50000,
        base_market: float = 18000.0,
        region: str = "EU",
    ) -> dict[str, Any]:
        if not vin and not (make and model):
            raise ValidationError("vin or make/model required")
        adj = max(0.4, 1.0 - mileage / 280000.0)
        market = round(float(base_market) * adj, 2)
        wholesale = round(market * 0.88, 2)
        retail = round(market * 1.08, 2)
        dealer = round(market * 1.02, 2)
        auction = round(market * 0.92, 2)
        export = round(market * 0.95, 2)
        import_p = round(market * 1.12, 2)
        future = round(market * 0.90, 2)
        rid = _id("sai_price")
        result = {
            "quote_id": rid,
            "vin": (vin or "").strip().upper(),
            "make": make,
            "model": model,
            "year": year,
            "mileage": mileage,
            "region": region,
            "market_price": market,
            "wholesale_price": wholesale,
            "retail_price": retail,
            "dealer_price": dealer,
            "auction_price": auction,
            "export_price": export,
            "import_price": import_p,
            "future_price_prediction": future,
            "currency": "USD",
            "at": _now(),
        }
        return self.store.sa_price_quotes.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"quotes": self.store.sa_price_quotes.count()}
