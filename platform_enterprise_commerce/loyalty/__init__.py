"""Loyalty Engine — Sprint 22.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_commerce.models import LOYALTY_LEVELS


class LoyaltyEngine:
    def profile(self, *, customer_id: str, points: float = 0.0) -> dict[str, Any]:
        if not customer_id:
            raise ValueError("customer_id is required")
        level = "new"
        if points >= 1000:
            level = "platinum"
        elif points >= 500:
            level = "gold"
        elif points >= 200:
            level = "silver"
        elif points >= 50:
            level = "bronze"
        return {
            "customer_id": customer_id,
            "points": float(points),
            "level": level,
            "levels": list(LOYALTY_LEVELS),
            "personal_discount_pct": {"new": 0, "bronze": 0.03, "silver": 0.05, "gold": 0.08, "platinum": 0.12}[level],
            "cashback_pct": 0.02,
            "promos_enabled": True,
            "accumulator": True,
        }

    def earn(self, profile: dict[str, Any], *, amount: float) -> dict[str, Any]:
        points = float(profile.get("points", 0)) + float(amount) * float(profile.get("cashback_pct", 0.02))
        return self.profile(customer_id=profile["customer_id"], points=points)

    def redeem(self, profile: dict[str, Any], *, points: float) -> dict[str, Any]:
        current = float(profile.get("points", 0))
        if points <= 0 or points > current:
            raise ValueError("invalid bonus redeem amount")
        return self.profile(customer_id=profile["customer_id"], points=current - points)
