"""Loyalty Center (portal view) — Sprint 22.8."""

from __future__ import annotations

from typing import Any


class LoyaltyCenter:
    def view(self, *, loyalty: dict[str, Any] | None = None, offers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        loyalty = loyalty or {"points": 0, "level": "new"}
        return {
            "balance": float(loyalty.get("points", loyalty.get("bonuses", 0)) or 0),
            "level": loyalty.get("level", "new"),
            "earn_history": list(loyalty.get("earn_history") or []),
            "redeem_history": list(loyalty.get("redeem_history") or []),
            "personal_offers": list(offers or []),
            "commerce_ref": "commerce_core",
        }
