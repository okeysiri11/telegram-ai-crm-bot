"""Repair / cost estimation — Sprint 13.2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

_BASE_COSTS = {
    "dent": 350,
    "scratch": 180,
    "paint_thickness": 220,
    "rust": 480,
    "corrosion": 620,
    "crack": 400,
    "frame": 2500,
    "flood": 4000,
    "fire": 6000,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RepairEstimation:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def estimate(
        self,
        *,
        vin: str = "",
        damages: list[dict[str, Any]] | None = None,
        market_value: float = 20000.0,
    ) -> dict[str, Any]:
        damages = damages or []
        parts = 0.0
        labor = 0.0
        hours = 0.0
        for d in damages:
            dtype = d.get("damage_type", "scratch")
            sev = float(d.get("severity", 0.3))
            base = float(_BASE_COSTS.get(dtype, 200))
            line = base * (0.5 + sev)
            parts += line * 0.55
            labor += line * 0.45
            hours += 1.5 + sev * 4
        repair_cost = round(parts + labor, 2)
        insurance = round(repair_cost * 0.92, 2)
        market_adj = round(market_value - repair_cost * 0.6, 2)
        residual = round(max(0.0, market_adj * 0.88), 2)
        rid = _id("iaest")
        result = {
            "estimate_id": rid,
            "vin": (vin or "").strip().upper(),
            "parts_cost": round(parts, 2),
            "labor_cost": round(labor, 2),
            "repair_cost": repair_cost,
            "insurance_estimate": insurance,
            "market_value_adjustment": market_adj,
            "residual_value_prediction": residual,
            "repair_time_hours": round(hours, 1),
            "currency": "USD",
            "damage_count": len(damages),
            "estimated_at": _now(),
        }
        return self.store.ia_estimates.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"estimates": self.store.ia_estimates.count()}
