"""Crop AI Suite facade — Sprint 14.3."""

from __future__ import annotations

from typing import Any

from applications.agro_enterprise.config import DEFAULT_CONFIG
from applications.agro_enterprise.crop_ai.intelligence import CropIntelligence, DiseaseDetectionAI, PestIntelligence
from applications.agro_enterprise.crop_ai.operations import (
    AIDecisionSupport,
    AutonomousFarmOps,
    CropAIDashboard,
    CropAIKnowledge,
    YieldIntelligence,
)
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store


class CropAISuite:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.crops = CropIntelligence(self.store)
        self.disease = DiseaseDetectionAI(self.store)
        self.pests = PestIntelligence(self.store)
        self.yield_intel = YieldIntelligence(self.store)
        self.ops = AutonomousFarmOps(self.store)
        self.decisions = AIDecisionSupport(self.store)
        self.dashboard = CropAIDashboard(self.store)
        self.knowledge = CropAIKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        crop = self.crops.register_crop(name="Winter Wheat", variety="Bohdana", field_id="field_north")
        self.crops.track_stage(crop["crop_id"], stage="vegetative", phenology_day=35)
        self.crops.track_stage(crop["crop_id"], stage="reproductive", phenology_day=70)
        self.crops.health(crop["crop_id"], health_score=78)
        ready = self.crops.harvest_readiness(crop["crop_id"])

        disease = self.disease.detect(
            crop_id=crop["crop_id"], part="leaf", disease_type="fungal", confidence=0.86, severity=0.35
        )
        self.disease.detect(crop_id=crop["crop_id"], part="stem", disease_type="bacterial", confidence=0.7, severity=0.2)

        pest = self.pests.identify(crop_id=crop["crop_id"], pest_name="aphid", population_index=0.55)
        self.pests.risk_map(region="EU-East")

        yield_pred = self.yield_intel.predict(
            crop_id=crop["crop_id"], hectares=48, health_score=78, ndvi=0.61, region="EU-East"
        )

        task = self.ops.plan_task(field_id="field_north", title="Scout disease edges", task_type="scout")
        mission = self.ops.schedule_mission(
            field_id="field_north", mission_type="spray", assignee="sprayer_01", starts_at="2026-07-24T05:30:00Z"
        )
        self.ops.assign(mission["mission_id"], asset="drone_scout_2", asset_kind="drone")
        self.ops.schedule_mission(field_id="field_north", mission_type="fertilize", assignee="spreader_1")
        self.ops.schedule_mission(field_id="field_north", mission_type="harvest", assignee="combine_1")

        rec = self.decisions.recommend(crop_id=crop["crop_id"], intent="treatment", context={"risk_score": 0.4})
        self.decisions.recommend(crop_id=crop["crop_id"], intent="harvest")

        for rtype, key in (
            ("crop", crop["crop_id"]),
            ("disease", disease["detection_id"]),
            ("pest", pest["pest_id"]),
            ("yield", yield_pred["prediction_id"]),
            ("autonomous_ops", mission["mission_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="ai_recommendation")
        return {
            "bootstrap": True,
            "crop_id": crop["crop_id"],
            "readiness_id": ready["readiness_id"],
            "detection_id": disease["detection_id"],
            "pest_id": pest["pest_id"],
            "yield_prediction_id": yield_pred["prediction_id"],
            "task_id": task["task_id"],
            "mission_id": mission["mission_id"],
            "recommendation_id": rec["recommendation_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "crops": self.crops.status(),
            "disease": self.disease.status(),
            "pests": self.pests.status(),
            "yield": self.yield_intel.status(),
            "ops": self.ops.status(),
            "decisions": self.decisions.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


crop_ai = CropAISuite()
