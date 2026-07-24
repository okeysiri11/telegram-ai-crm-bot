"""Recommendation Comparator — Sprint 24.4."""

from __future__ import annotations

from typing import Any


class RecommendationComparator:
    def compare(self, *, options: list[dict[str, Any]]) -> dict[str, Any]:
        if not options:
            raise ValueError("at least one option required")
        compared = []
        for opt in options:
            compared.append(
                {
                    "option_id": opt.get("option_id") or opt.get("name"),
                    "pros": list(opt.get("pros") or ["upside"]),
                    "cons": list(opt.get("cons") or ["cost"]),
                    "cost": float(opt.get("cost", 0)),
                    "risks": float(opt.get("risks", 0.2)),
                    "expected_profit": float(opt.get("expected_profit", 0)),
                    "payback_days": int(opt.get("payback_days", 90)),
                }
            )
        ranked = sorted(compared, key=lambda x: x["expected_profit"] - x["cost"] * x["risks"], reverse=True)
        return {"options": compared, "ranked": ranked, "best": ranked[0] if ranked else None}
