"""Inspection reports, knowledge links, dashboards — Sprint 13.2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

DASHBOARD_TYPES = ["inspection", "damage", "repair", "vehicle_health"]
KNOWLEDGE_SOURCES = [
    "vehicle_passport",
    "vin_intelligence",
    "maintenance_history",
    "market_analytics",
    "dealer_database",
    "insurance_database",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class InspectionReport:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def generate(
        self,
        *,
        vin: str,
        health: dict[str, Any] | None = None,
        estimate: dict[str, Any] | None = None,
        damages: list[dict[str, Any]] | None = None,
        format: str = "pdf",
    ) -> dict[str, Any]:
        if format not in ("pdf", "json"):
            raise ValidationError("format must be pdf or json")
        vin = (vin or "").strip().upper()
        health = health or {}
        estimate = estimate or {}
        damages = damages or []
        overall = float(health.get("overall_condition_score", 70))
        purchase = "buy" if overall >= 75 and float(estimate.get("repair_cost", 0)) < 3000 else "negotiate" if overall >= 55 else "avoid"
        repair = "repair_now" if float(estimate.get("repair_cost", 0)) > 500 else "monitor"
        insurance = "file_claim" if float(estimate.get("insurance_estimate", 0)) > 1500 else "self_pay"
        dealer = "accept_trade" if overall >= 65 else "wholesale_only"
        rid = _id("iarpt")
        report = {
            "report_id": rid,
            "vin": vin,
            "format": format,
            "professional_pdf": format == "pdf",
            "damage_map": [{"type": d.get("damage_type"), "location": d.get("location"), "severity": d.get("severity")} for d in damages],
            "risk_summary": {
                "overall_score": overall,
                "high_severity_count": len([d for d in damages if float(d.get("severity", 0)) >= 0.7]),
            },
            "ai_recommendations": {
                "purchase": purchase,
                "repair": repair,
                "insurance": insurance,
                "dealer": dealer,
            },
            "health_ref": health.get("score_id"),
            "estimate_ref": estimate.get("estimate_id"),
            "generated_at": _now(),
        }
        return self.store.ia_reports.save(rid, report)

    def get(self, report_id: str) -> dict[str, Any]:
        item = self.store.ia_reports.get(report_id)
        if item is None:
            raise NotFoundError("report", report_id)
        return item

    def status(self) -> dict[str, Any]:
        return {"reports": self.store.ia_reports.count()}


class KnowledgeIntegration:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.sources = list(KNOWLEDGE_SOURCES)

    def link(self, *, vin: str, source: str, ref_id: str = "", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if source not in self.sources:
            raise ValidationError(f"source must be one of {self.sources}")
        lid = _id("iaknow")
        record = {
            "link_id": lid,
            "vin": (vin or "").strip().upper(),
            "source": source,
            "ref_id": ref_id,
            "payload": payload or {},
            "linked_at": _now(),
        }
        return self.store.ia_knowledge_links.save(lid, record)

    def status(self) -> dict[str, Any]:
        return {"links": self.store.ia_knowledge_links.count(), "sources": self.sources}


class InspectionDashboard:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        if dashboard_type == "inspection":
            widgets: dict[str, Any] = {
                "photo_analyses": self.store.ia_photo_analyses.count(),
                "reports": self.store.ia_reports.count(),
            }
        elif dashboard_type == "damage":
            widgets = {
                "detections": self.store.ia_damages.count(),
                "high_severity": len([d for d in self.store.ia_damages.list_all() if float(d.get("severity", 0)) >= 0.7]),
            }
        elif dashboard_type == "repair":
            estimates = self.store.ia_estimates.list_all()
            avg = round(sum(float(e.get("repair_cost") or 0) for e in estimates) / max(1, len(estimates)), 2)
            widgets = {"estimates": len(estimates), "avg_repair_cost": avg}
        else:
            scores = self.store.ia_health_scores.list_all()
            avg = round(sum(float(s.get("overall_condition_score") or 0) for s in scores) / max(1, len(scores)), 1)
            widgets = {"scores": len(scores), "avg_overall": avg}
        did = _id("iadash")
        board = {
            "dashboard_id": did,
            "dashboard_type": dashboard_type,
            "widgets": widgets,
            "rendered_at": _now(),
        }
        return self.store.ia_dashboards.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ia_dashboards.count(), "types": self.types}
