"""Optimization Registry — Sprint 24.6."""

from __future__ import annotations

from typing import Any

from platform_enterprise_autonomous_optimization.models import CATEGORIES, OWNER_STATUSES


class OptimizationRegistry:
    def create(
        self,
        *,
        opportunity_id: str,
        category: str,
        title: str,
        priority: str = "medium",
        business_value: float = 0.0,
        expected_roi: float = 0.0,
        confidence: float = 0.7,
        risk_score: float = 0.3,
    ) -> dict[str, Any]:
        if not opportunity_id or not title:
            raise ValueError("opportunity_id and title are required")
        category = (category or "").lower()
        if category not in CATEGORIES:
            raise ValueError(f"unsupported category: {category}")
        return {
            "opportunity_id": opportunity_id,
            "category": category,
            "title": title.strip(),
            "priority": priority,
            "business_value": float(business_value),
            "expected_roi": float(expected_roi),
            "confidence_score": float(confidence),
            "risk_score": float(risk_score),
            "owner_status": "proposed",
            "implementation_history": [],
        }

    def set_status(self, opportunity: dict[str, Any], *, status: str) -> dict[str, Any]:
        status = (status or "").lower()
        if status not in OWNER_STATUSES:
            raise ValueError(f"unsupported status: {status}")
        updated = dict(opportunity)
        updated["owner_status"] = status
        return updated

    def record_implementation(self, opportunity: dict[str, Any], *, note: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
        updated = dict(opportunity)
        hist = list(updated.get("implementation_history") or [])
        hist.append({"note": note, "result": dict(result or {})})
        updated["implementation_history"] = hist[-50:]
        return updated
