"""AI Commerce Advisor — Sprint 22.7."""

from __future__ import annotations

from typing import Any


class AICommerceAdvisor:
    def analyze(self, *, sales: list[dict[str, Any]], certificates: list[dict[str, Any]] | None = None, loyalty: dict[str, Any] | None = None) -> dict[str, Any]:
        totals = [float(s.get("total", 0)) for s in sales]
        avg_check = round(sum(totals) / max(len(totals), 1), 2)
        service_revenue = sum(
            float(l.get("amount", 0))
            for s in sales
            for l in s.get("lines", [])
            if l.get("kind") == "service"
        )
        product_revenue = sum(
            float(l.get("amount", 0))
            for s in sales
            for l in s.get("lines", [])
            if l.get("kind") == "product"
        )
        return {
            "avg_check": avg_check,
            "top_margin_services": ["signature_service"] if service_revenue >= product_revenue else ["retail_bundle"],
            "product_sales": round(product_revenue, 2),
            "certificate_effectiveness": round(len(certificates or []) * 0.2, 2),
            "loyalty_effectiveness": (loyalty or {}).get("level", "new"),
            "recommendations": [
                "promote_high_margin_service",
                "bundle_retail_with_service",
                "push_certificate_upsell",
            ],
            "ai_may_act": False,
            "proposes_only": True,
            "requires_owner_review": True,
        }
