"""Inspection AI Suite facade — Sprint 13.2."""

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.inspection_ai.damage import DamageDetection
from applications.auto_marketplace.inspection_ai.estimation import RepairEstimation
from applications.auto_marketplace.inspection_ai.health import VehicleHealthScore
from applications.auto_marketplace.inspection_ai.photo import PhotoInspection
from applications.auto_marketplace.inspection_ai.services import (
    InspectionDashboard,
    InspectionReport,
    KnowledgeIntegration,
)
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class InspectionAISuite:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.photo = PhotoInspection(self.store)
        self.damage = DamageDetection(self.store)
        self.estimation = RepairEstimation(self.store)
        self.health = VehicleHealthScore(self.store)
        self.report = InspectionReport(self.store)
        self.knowledge = KnowledgeIntegration(self.store)
        self.dashboard = InspectionDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        vin = "WVWZZZ1JZXW000001"
        photos = []
        for zone in ("exterior", "interior", "engine_bay", "paint", "vin_plate"):
            photos.append(
                self.photo.analyze(
                    vin=vin,
                    zone=zone,
                    media_uri=f"media://{vin}/{zone}.jpg",
                    media_type="photo",
                    signals={"quality": 0.9},
                )
            )
        damages = self.damage.scan_all(
            vin=vin,
            signals={"dent": 0.35, "scratch": 0.45, "rust": 0.1, "frame": 0.05},
        )
        detected = [d for d in damages if d.get("detected")]
        estimate = self.estimation.estimate(vin=vin, damages=detected, market_value=18500)
        health = self.health.score(vin=vin, damages=detected, photo_quality_avg=0.9)
        report = self.report.generate(vin=vin, health=health, estimate=estimate, damages=detected, format="pdf")
        self.knowledge.link(vin=vin, source="vin_intelligence", ref_id="bootstrap", payload={"vin": vin})
        self.knowledge.link(vin=vin, source="vehicle_passport", ref_id="bootstrap")
        self.knowledge.link(vin=vin, source="market_analytics", payload={"market_value": 18500})
        board = self.dashboard.render(dashboard_type="inspection")
        return {
            "bootstrap": True,
            "vin": vin,
            "photo_analyses": len(photos),
            "damages_detected": len(detected),
            "estimate_id": estimate["estimate_id"],
            "score_id": health["score_id"],
            "report_id": report["report_id"],
            "dashboard_id": board["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "photo": self.photo.status(),
            "damage": self.damage.status(),
            "estimation": self.estimation.status(),
            "health": self.health.status(),
            "report": self.report.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


inspection_ai = InspectionAISuite()
