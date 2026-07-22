"""Yield intelligence, autonomous ops, decision support, dashboards, knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

MISSION_TYPES = ["spray", "fertilize", "harvest", "scout", "drone_survey"]
DASHBOARD_TYPES = ["crop_health", "disease", "pest", "yield", "farm_operations", "ai_recommendation"]
REGISTRY_TYPES = ["crop", "disease", "pest", "yield", "autonomous_ops"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class YieldIntelligence:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def predict(
        self,
        *,
        crop_id: str,
        hectares: float = 10.0,
        health_score: float = 80.0,
        ndvi: float = 0.6,
        region: str = "",
    ) -> dict[str, Any]:
        if self.store.ca_crops.get(crop_id) is None:
            raise NotFoundError("crop", crop_id)
        base = 3.5 + ndvi * 4 + health_score / 50
        loss = max(0.0, (90 - health_score) / 100)
        yield_t_ha = round(base * (1 - loss * 0.4), 2)
        quality = round(min(1.0, health_score / 100 * 0.7 + ndvi * 0.3), 3)
        pid = _id("ca_yield")
        result = {
            "prediction_id": pid,
            "crop_id": crop_id,
            "region": region,
            "hectares": float(hectares),
            "yield_t_ha": yield_t_ha,
            "total_t": round(yield_t_ha * hectares, 2),
            "quality_index": quality,
            "loss_probability": round(loss, 3),
            "harvest_forecast_days": 18 if health_score > 70 else 25,
            "at": _now(),
        }
        return self.store.ca_yields.save(pid, result)

    def history(self, crop_id: str = "") -> list[dict[str, Any]]:
        items = self.store.ca_yields.list_all()
        if crop_id:
            return [y for y in items if y.get("crop_id") == crop_id]
        return items

    def status(self) -> dict[str, Any]:
        return {"predictions": self.store.ca_yields.count()}


class AutonomousFarmOps:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.mission_types = list(MISSION_TYPES)

    def plan_task(self, *, field_id: str, title: str, task_type: str = "scout") -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        tid = _id("ca_task")
        return self.store.ca_tasks.save(
            tid,
            {
                "task_id": tid,
                "field_id": field_id,
                "title": title,
                "task_type": task_type,
                "status": "planned",
                "created_at": _now(),
            },
        )

    def schedule_mission(
        self,
        *,
        field_id: str,
        mission_type: str,
        assignee: str = "drone",
        starts_at: str = "",
    ) -> dict[str, Any]:
        if mission_type not in self.mission_types:
            raise ValidationError(f"mission_type must be one of {self.mission_types}")
        mid = _id("ca_mis")
        return self.store.ca_missions.save(
            mid,
            {
                "mission_id": mid,
                "field_id": field_id,
                "mission_type": mission_type,
                "assignee": assignee,
                "starts_at": starts_at or _now(),
                "status": "scheduled",
                "created_at": _now(),
            },
        )

    def assign(self, mission_id: str, *, asset: str, asset_kind: str = "drone") -> dict[str, Any]:
        mission = self.store.ca_missions.get(mission_id)
        if mission is None:
            raise NotFoundError("mission", mission_id)
        mission["assignee"] = asset
        mission["asset_kind"] = asset_kind
        mission["status"] = "assigned"
        mission["updated_at"] = _now()
        return self.store.ca_missions.save(mission_id, mission)

    def status(self) -> dict[str, Any]:
        return {
            "tasks": self.store.ca_tasks.count(),
            "missions": self.store.ca_missions.count(),
            "types": self.mission_types,
        }


class AIDecisionSupport:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def recommend(
        self,
        *,
        crop_id: str,
        intent: str = "treatment",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.store.ca_crops.get(crop_id) is None:
            raise NotFoundError("crop", crop_id)
        context = context or {}
        intents = {
            "crop": ["rotate_to_legume", "choose_drought_tolerant_variety"],
            "treatment": ["apply_fungicide_edge", "spot_treat_hotspots"],
            "nutrient": ["topdress_n", "foliar_micronutrients"],
            "harvest": ["delay_3_days", "priority_dry_windows"],
            "risk": ["increase_scouting", "prepare_irrigation_buffer"],
            "operations": ["schedule_spray_morning", "assign_drone_scout"],
        }
        if intent not in intents:
            raise ValidationError(f"intent must be one of {list(intents)}")
        rid = _id("ca_rec")
        return self.store.ca_recommendations.save(
            rid,
            {
                "recommendation_id": rid,
                "crop_id": crop_id,
                "intent": intent,
                "actions": intents[intent],
                "context": context,
                "risk_score": float(context.get("risk_score", 0.35) or 0.35),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"recommendations": self.store.ca_recommendations.count()}


class CropAIDashboard:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "crop_health") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "crop_health": {"crops": self.store.ca_crops.count()},
            "disease": {"detections": self.store.ca_diseases.count()},
            "pest": {"pests": self.store.ca_pests.count()},
            "yield": {"predictions": self.store.ca_yields.count()},
            "farm_operations": {"missions": self.store.ca_missions.count(), "tasks": self.store.ca_tasks.count()},
            "ai_recommendation": {"recommendations": self.store.ca_recommendations.count()},
        }[dashboard_type]
        did = _id("ca_dash")
        return self.store.ca_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ca_dashboards.count(), "types": self.types}


class CropAIKnowledge:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("ca_reg")
        return self.store.ca_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"crop_ai:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.ca_registries.count(), "types": self.types}
