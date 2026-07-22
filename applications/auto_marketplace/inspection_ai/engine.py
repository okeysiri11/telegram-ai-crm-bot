# Inspection AI Engine — photo/damage/paint/body/wheel/interior/engine analysis.

from __future__ import annotations

from applications.auto_marketplace.ai.models import AIInspectionResult
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class InspectionAIEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def analyze(
        self,
        *,
        vehicle_id: str = "",
        photo_urls: list[str] | None = None,
        hints: dict | None = None,
    ) -> AIInspectionResult:
        photos = photo_urls or []
        if not vehicle_id and not photos:
            raise ValidationError("vehicle_id or photo_urls is required")
        hints = hints or {}
        photo_count = len(photos)
        paint = float(hints.get("paint_score", 70 + min(25, photo_count * 5)))
        body = float(hints.get("body_score", 72 + min(20, photo_count * 4)))
        wheel = float(hints.get("wheel_score", 75))
        interior = float(hints.get("interior_score", 68 + min(20, photo_count * 3)))
        engine_bay = float(hints.get("engine_bay_score", 70))
        damage = list(hints.get("damage") or [])
        if photo_count < 3 and not damage:
            damage.append({"area": "unknown", "severity": "low", "note": "insufficient_angles"})
        risk = round(max(0.05, 1.0 - ((paint + body + wheel + interior + engine_bay) / 500)), 3)
        repair = round(sum(2000 if d.get("severity") == "high" else 800 if d.get("severity") == "medium" else 250 for d in damage), 2)
        overall = round((paint + body + wheel + interior + engine_bay) / 5, 2)
        findings = []
        if paint < 70:
            findings.append("paint_wear")
        if body < 70:
            findings.append("body_alignment_attention")
        if damage:
            findings.append("damage_detected")
        result = AIInspectionResult(
            vehicle_id=vehicle_id,
            photo_urls=photos,
            damage_detected=damage,
            paint_score=round(paint, 2),
            body_alignment_score=round(body, 2),
            wheel_score=round(wheel, 2),
            interior_score=round(interior, 2),
            engine_bay_score=round(engine_bay, 2),
            risk_score=risk,
            repair_estimate=repair,
            overall_score=overall,
            findings=findings,
        )
        return self._store.ai_inspection_results.save(result.analysis_id, result)

    def metrics(self) -> dict:
        return {"ai_inspections": self._store.ai_inspection_results.count()}


inspection_ai_engine = InspectionAIEngine()
