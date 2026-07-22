"""AI irrigation, environmental intelligence, dashboards, knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

DASHBOARD_TYPES = ["irrigation", "water", "soil", "sensor", "ai_recommendation"]
REGISTRY_TYPES = ["soil", "water", "irrigation", "sensor", "environmental"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIIrrigation:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def predict(
        self,
        *,
        zone_id: str,
        soil_moisture_pct: float = 30.0,
        et0_mm: float = 4.5,
        forecast_rain_mm: float = 0.0,
        water_cost_per_m3: float = 0.4,
    ) -> dict[str, Any]:
        demand = max(0.0, et0_mm * 1.1 - forecast_rain_mm * 0.7 - max(0, soil_moisture_pct - 25) * 0.05)
        drought = min(0.95, max(0.05, (35 - soil_moisture_pct) / 40 + et0_mm / 20))
        recommend_mm = round(demand, 2)
        cost = round(recommend_mm * 10 * water_cost_per_m3 / 1000, 3)
        pid = _id("si_ai")
        return self.store.si_ai_predictions.save(
            pid,
            {
                "prediction_id": pid,
                "zone_id": zone_id,
                "water_demand_mm": recommend_mm,
                "irrigation_recommendation": "irrigate" if recommend_mm > 2 else "hold",
                "optimal_distribution": {"priority_zones": [zone_id], "mm": recommend_mm},
                "evapotranspiration_mm": float(et0_mm),
                "drought_risk": round(drought, 3),
                "estimated_cost": cost,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"predictions": self.store.si_ai_predictions.count()}


class EnvironmentalIntelligence:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def ingest_weather(
        self,
        *,
        region: str,
        temp_c: float = 22.0,
        humidity_pct: float = 55.0,
        rain_mm: float = 0.0,
        wind_ms: float = 3.0,
    ) -> dict[str, Any]:
        wid = _id("si_wx")
        return self.store.si_weather.save(
            wid,
            {
                "weather_id": wid,
                "region": region,
                "temp_c": float(temp_c),
                "humidity_pct": float(humidity_pct),
                "rain_mm": float(rain_mm),
                "wind_ms": float(wind_ms),
                "at": _now(),
            },
        )

    def assess_risks(self, *, region: str, soil_moisture_pct: float = 30.0, temp_c: float = 30.0) -> dict[str, Any]:
        rid = _id("si_risk")
        return self.store.si_env_risks.save(
            rid,
            {
                "risk_id": rid,
                "region": region,
                "water_stress": round(max(0.0, (28 - soil_moisture_pct) / 28), 3),
                "heat_stress": round(max(0.0, (temp_c - 28) / 15), 3),
                "flood_risk": 0.1 if soil_moisture_pct > 55 else 0.02,
                "microclimate": {"band": "warm" if temp_c > 25 else "mild"},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"weather": self.store.si_weather.count(), "risks": self.store.si_env_risks.count()}


class IrrigationDashboard:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "irrigation") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "irrigation": {"zones": self.store.si_zones.count(), "schedules": self.store.si_schedules.count()},
            "water": {"sources": self.store.si_water_sources.count(), "consumption": self.store.si_consumption.count()},
            "soil": {"soils": self.store.si_soils.count(), "nutrient_analyses": self.store.si_nutrient_analyses.count()},
            "sensor": {"sensors": self.store.si_iot_sensors.count(), "gateways": self.store.si_gateways.count()},
            "ai_recommendation": {"predictions": self.store.si_ai_predictions.count()},
        }[dashboard_type]
        did = _id("si_dash")
        return self.store.si_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.si_dashboards.count(), "types": self.types}


class IrrigationKnowledge:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("si_reg")
        return self.store.si_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"irrigation:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.si_registries.count(), "types": self.types}
