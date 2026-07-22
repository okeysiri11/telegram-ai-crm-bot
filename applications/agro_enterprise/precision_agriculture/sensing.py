"""Drone integration, satellite intelligence, IoT smart farming."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

SENSOR_KINDS = ["weather", "soil_moisture", "temperature", "humidity", "water_level", "irrigation"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DroneIntegration:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def plan_mission(
        self,
        *,
        field_id: str,
        mission_type: str = "survey",
        altitude_m: float = 80.0,
    ) -> dict[str, Any]:
        if self.store.pa_fields.get(field_id) is None:
            raise NotFoundError("field", field_id)
        mid = _id("pa_mission")
        return self.store.pa_drone_missions.save(
            mid,
            {
                "mission_id": mid,
                "field_id": field_id,
                "mission_type": mission_type,
                "altitude_m": float(altitude_m),
                "status": "planned",
                "drone_platform_bridge": "/api/drone/v1",
                "created_at": _now(),
            },
        )

    def complete_survey(
        self,
        mission_id: str,
        *,
        orthomosaic: bool = True,
        multispectral: bool = True,
        thermal: bool = False,
        plant_count: int = 0,
    ) -> dict[str, Any]:
        mission = self.store.pa_drone_missions.get(mission_id)
        if mission is None:
            raise NotFoundError("mission", mission_id)
        mission["status"] = "completed"
        mission["orthomosaic"] = bool(orthomosaic)
        mission["multispectral"] = bool(multispectral)
        mission["thermal"] = bool(thermal)
        mission["plant_count"] = int(plant_count)
        mission["completed_at"] = _now()
        self.store.pa_drone_missions.save(mission_id, mission)
        aid = _id("pa_flight")
        archive = {
            "flight_id": aid,
            "mission_id": mission_id,
            "field_id": mission["field_id"],
            "assets": {
                "orthomosaic": orthomosaic,
                "multispectral": multispectral,
                "thermal": thermal,
            },
            "at": _now(),
        }
        return self.store.pa_flight_archive.save(aid, archive)

    def status(self) -> dict[str, Any]:
        return {
            "missions": self.store.pa_drone_missions.count(),
            "flights": self.store.pa_flight_archive.count(),
        }


class SatelliteIntelligence:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def ingest_imagery(self, *, field_id: str, source: str = "sentinel-2", captured_at: str = "") -> dict[str, Any]:
        if self.store.pa_fields.get(field_id) is None:
            raise NotFoundError("field", field_id)
        iid = _id("pa_sat")
        return self.store.pa_satellite.save(
            iid,
            {
                "imagery_id": iid,
                "field_id": field_id,
                "source": source,
                "captured_at": captured_at or _now(),
                "created_at": _now(),
            },
        )

    def analyze(self, imagery_id: str) -> dict[str, Any]:
        img = self.store.pa_satellite.get(imagery_id)
        if img is None:
            raise NotFoundError("imagery", imagery_id)
        aid = _id("pa_satan")
        result = {
            "analysis_id": aid,
            "imagery_id": imagery_id,
            "field_id": img["field_id"],
            "ndvi": 0.62,
            "ndre": 0.48,
            "vegetation_health": "good",
            "moisture_index": 0.55,
            "weather_overlay": {"cloud_cover_pct": 12},
            "at": _now(),
        }
        return self.store.pa_sat_analysis.save(aid, result)

    def timeline(self, field_id: str) -> list[dict[str, Any]]:
        return [i for i in self.store.pa_satellite.list_all() if i.get("field_id") == field_id]

    def status(self) -> dict[str, Any]:
        return {"imagery": self.store.pa_satellite.count(), "analyses": self.store.pa_sat_analysis.count()}


class IoTSmartFarming:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.kinds = list(SENSOR_KINDS)

    def register_sensor(self, *, field_id: str, kind: str, name: str = "") -> dict[str, Any]:
        if kind not in self.kinds:
            raise ValidationError(f"kind must be one of {self.kinds}")
        if self.store.pa_fields.get(field_id) is None:
            raise NotFoundError("field", field_id)
        sid = _id("pa_iot")
        return self.store.pa_sensors.save(
            sid,
            {
                "sensor_id": sid,
                "field_id": field_id,
                "kind": kind,
                "name": name or kind,
                "status": "online",
                "created_at": _now(),
            },
        )

    def reading(self, sensor_id: str, *, value: float, unit: str = "") -> dict[str, Any]:
        sensor = self.store.pa_sensors.get(sensor_id)
        if sensor is None:
            raise NotFoundError("sensor", sensor_id)
        rid = _id("pa_read")
        return self.store.pa_sensor_readings.save(
            rid,
            {
                "reading_id": rid,
                "sensor_id": sensor_id,
                "field_id": sensor["field_id"],
                "kind": sensor["kind"],
                "value": float(value),
                "unit": unit,
                "at": _now(),
            },
        )

    def irrigate(self, *, field_id: str, duration_min: int = 30) -> dict[str, Any]:
        if self.store.pa_fields.get(field_id) is None:
            raise NotFoundError("field", field_id)
        cid = _id("pa_irr")
        return self.store.pa_irrigation.save(
            cid,
            {
                "command_id": cid,
                "field_id": field_id,
                "duration_min": int(duration_min),
                "status": "started",
                "at": _now(),
            },
        )

    def dashboard(self, field_id: str = "") -> dict[str, Any]:
        sensors = self.store.pa_sensors.list_all()
        if field_id:
            sensors = [s for s in sensors if s.get("field_id") == field_id]
        return {
            "field_id": field_id or "all",
            "sensors": len(sensors),
            "online": len([s for s in sensors if s.get("status") == "online"]),
            "readings": self.store.pa_sensor_readings.count(),
            "irrigation_commands": self.store.pa_irrigation.count(),
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "sensors": self.store.pa_sensors.count(),
            "readings": self.store.pa_sensor_readings.count(),
            "kinds": self.kinds,
        }
