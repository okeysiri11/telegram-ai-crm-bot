"""Vehicle health scoring — Sprint 13.2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class VehicleHealthScore:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def score(
        self,
        *,
        vin: str = "",
        damages: list[dict[str, Any]] | None = None,
        photo_quality_avg: float = 0.85,
    ) -> dict[str, Any]:
        damages = damages or []
        penalty = sum(float(d.get("severity", 0)) * 12 for d in damages)
        body = max(0.0, 95 - penalty)
        paint = max(0.0, 92 - sum(8 for d in damages if d.get("damage_type") in ("scratch", "paint_thickness", "rust")))
        interior = max(0.0, 90 - sum(5 for d in damages if d.get("location") == "interior"))
        mechanical = max(0.0, 88 - sum(15 for d in damages if d.get("damage_type") in ("flood", "fire", "frame")))
        electrical = max(0.0, 90 - sum(20 for d in damages if d.get("damage_type") == "flood"))
        safety = max(0.0, 93 - sum(18 for d in damages if d.get("damage_type") in ("frame", "crack")))
        overall = round(
            (body + paint + interior + mechanical + electrical + safety) / 6 * (0.9 + 0.1 * photo_quality_avg),
            1,
        )
        rid = _id("iahlth")
        result = {
            "score_id": rid,
            "vin": (vin or "").strip().upper(),
            "mechanical_score": round(mechanical, 1),
            "body_score": round(body, 1),
            "paint_score": round(paint, 1),
            "interior_score": round(interior, 1),
            "electrical_score": round(electrical, 1),
            "safety_score": round(safety, 1),
            "overall_condition_score": overall,
            "scored_at": _now(),
        }
        return self.store.ia_health_scores.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"scores": self.store.ia_health_scores.count()}
