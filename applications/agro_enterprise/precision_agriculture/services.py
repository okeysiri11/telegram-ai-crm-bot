"""AI crop monitoring, dashboards, knowledge registries."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

DASHBOARD_TYPES = ["field", "drone", "satellite", "iot", "crop_health"]
REGISTRY_TYPES = ["field", "crop_monitoring", "drone_mission", "satellite", "sensor"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AICropMonitoring:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def analyze(
        self,
        *,
        field_id: str,
        ndvi: float = 0.6,
        stress_index: float = 0.2,
        growth_day: int = 60,
    ) -> dict[str, Any]:
        if self.store.pa_fields.get(field_id) is None:
            raise NotFoundError("field", field_id)
        disease = round(max(0.0, stress_index * 0.8 + max(0, 0.45 - ndvi)), 3)
        pest = round(max(0.0, stress_index * 0.5), 3)
        nutrient = round(max(0.0, 0.55 - ndvi), 3)
        weed = round(max(0.0, 0.3 - ndvi * 0.2), 3)
        stage = "vegetative" if growth_day < 45 else "reproductive" if growth_day < 90 else "maturity"
        yield_t = round(4.0 + ndvi * 3.5 - stress_index * 2, 2)
        harvest_ready = growth_day >= 100 and ndvi < 0.55
        aid = _id("pa_ai")
        result = {
            "analysis_id": aid,
            "field_id": field_id,
            "disease_probability": disease,
            "pest_probability": pest,
            "nutrient_deficiency_probability": nutrient,
            "weed_probability": weed,
            "growth_stage": stage,
            "yield_prediction_t_ha": yield_t,
            "harvest_readiness": harvest_ready,
            "at": _now(),
        }
        return self.store.pa_ai_monitoring.save(aid, result)

    def status(self) -> dict[str, Any]:
        return {"analyses": self.store.pa_ai_monitoring.count()}


class PrecisionDashboard:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "field") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "field": {"fields": self.store.pa_fields.count(), "maps": self.store.pa_maps.count()},
            "drone": {"missions": self.store.pa_drone_missions.count(), "flights": self.store.pa_flight_archive.count()},
            "satellite": {"imagery": self.store.pa_satellite.count(), "analyses": self.store.pa_sat_analysis.count()},
            "iot": {"sensors": self.store.pa_sensors.count(), "readings": self.store.pa_sensor_readings.count()},
            "crop_health": {"ai_analyses": self.store.pa_ai_monitoring.count()},
        }[dashboard_type]
        did = _id("pa_dash")
        return self.store.pa_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.pa_dashboards.count(), "types": self.types}


class PrecisionKnowledge:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("pa_reg")
        return self.store.pa_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"precision:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.pa_registries.count(), "types": self.types}
