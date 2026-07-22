"""Trade-In AI — Sprint 13.3."""

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


class TradeInAI:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def evaluate(
        self,
        *,
        vin: str,
        mileage: int = 50000,
        damage_score: float = 0.2,
        market_value: float = 18000.0,
        inspection_ref: str = "",
        vin_decode_ref: str = "",
        target_margin: float = 0.12,
    ) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("vin required for trade-in evaluation")
        damage_score = max(0.0, min(1.0, float(damage_score)))
        adj = max(0.4, 1.0 - mileage / 280000.0 - damage_score * 0.25)
        residual = round(float(market_value) * adj, 2)
        margin = round(residual * float(target_margin), 2)
        offer = round(residual - margin, 2)
        negotiation = {
            "floor": round(offer * 0.95, 2),
            "target": offer,
            "ceiling": round(offer * 1.05, 2),
            "talking_points": [
                "Reference inspection damage score",
                "Highlight mileage vs segment average",
                "Anchor to residual forecast",
            ],
        }
        rid = _id("dcrm_ti")
        result = {
            "evaluation_id": rid,
            "vin": vin,
            "mileage": mileage,
            "damage_score": damage_score,
            "market_value": float(market_value),
            "residual_value": residual,
            "dealer_margin": margin,
            "trade_in_offer": offer,
            "negotiation_assistant": negotiation,
            "inspection_ref": inspection_ref,
            "vin_decode_ref": vin_decode_ref,
            "evaluated_at": _now(),
        }
        return self.store.dc_tradeins.save(rid, result)

    def generate_offer(self, evaluation_id: str, *, customer_id: str = "") -> dict[str, Any]:
        evaluation = self.store.dc_tradeins.get(evaluation_id)
        if evaluation is None:
            raise ValidationError(f"evaluation not found: {evaluation_id}")
        oid = _id("dcrm_offer")
        offer = {
            "offer_id": oid,
            "evaluation_id": evaluation_id,
            "customer_id": customer_id,
            "vin": evaluation["vin"],
            "amount": evaluation["trade_in_offer"],
            "currency": "USD",
            "status": "issued",
            "issued_at": _now(),
        }
        return self.store.dc_tradein_offers.save(oid, offer)

    def status(self) -> dict[str, Any]:
        return {
            "evaluations": self.store.dc_tradeins.count(),
            "offers": self.store.dc_tradein_offers.count(),
        }
