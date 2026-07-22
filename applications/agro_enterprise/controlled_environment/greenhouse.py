"""Greenhouse management and controlled environment AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

CLIMATE_CONTROLS = ["lighting", "ventilation", "heating", "cooling"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class GreenhouseManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_greenhouse(self, *, name: str, area_m2: float = 1000.0, location: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("greenhouse name required")
        gid = _id("ce_gh")
        return self.store.ce_greenhouses.save(
            gid,
            {
                "greenhouse_id": gid,
                "name": name,
                "area_m2": float(area_m2),
                "location": location,
                "created_at": _now(),
            },
        )

    def create_zone(self, *, greenhouse_id: str, name: str) -> dict[str, Any]:
        if self.store.ce_greenhouses.get(greenhouse_id) is None:
            raise NotFoundError("greenhouse", greenhouse_id)
        zid = _id("ce_zone")
        return self.store.ce_zones.save(
            zid,
            {
                "zone_id": zid,
                "greenhouse_id": greenhouse_id,
                "name": name,
                "temp_c": 22.0,
                "humidity_pct": 65.0,
                "co2_ppm": 800.0,
                "created_at": _now(),
            },
        )

    def set_climate(self, zone_id: str, *, temp_c: float | None = None, humidity_pct: float | None = None, co2_ppm: float | None = None) -> dict[str, Any]:
        zone = self.store.ce_zones.get(zone_id)
        if zone is None:
            raise NotFoundError("zone", zone_id)
        if temp_c is not None:
            zone["temp_c"] = float(temp_c)
        if humidity_pct is not None:
            zone["humidity_pct"] = float(humidity_pct)
        if co2_ppm is not None:
            zone["co2_ppm"] = float(co2_ppm)
        zone["updated_at"] = _now()
        return self.store.ce_zones.save(zone_id, zone)

    def control(self, zone_id: str, *, control: str, enabled: bool, setpoint: float | None = None) -> dict[str, Any]:
        if control not in CLIMATE_CONTROLS:
            raise ValidationError(f"control must be one of {CLIMATE_CONTROLS}")
        if self.store.ce_zones.get(zone_id) is None:
            raise NotFoundError("zone", zone_id)
        cid = _id("ce_ctrl")
        return self.store.ce_controls.save(
            cid,
            {
                "control_id": cid,
                "zone_id": zone_id,
                "control": control,
                "enabled": bool(enabled),
                "setpoint": setpoint,
                "at": _now(),
            },
        )

    def schedule_crop(self, *, zone_id: str, crop: str, starts_at: str, ends_at: str = "") -> dict[str, Any]:
        if self.store.ce_zones.get(zone_id) is None:
            raise NotFoundError("zone", zone_id)
        sid = _id("ce_sched")
        return self.store.ce_crop_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "zone_id": zone_id,
                "crop": crop,
                "starts_at": starts_at,
                "ends_at": ends_at,
                "status": "active",
                "created_at": _now(),
            },
        )

    def record_yield(self, *, zone_id: str, kg: float) -> dict[str, Any]:
        if self.store.ce_zones.get(zone_id) is None:
            raise NotFoundError("zone", zone_id)
        yid = _id("ce_yield")
        return self.store.ce_yields.save(
            yid, {"yield_id": yid, "zone_id": zone_id, "kg": float(kg), "at": _now()}
        )

    def status(self) -> dict[str, Any]:
        return {
            "greenhouses": self.store.ce_greenhouses.count(),
            "zones": self.store.ce_zones.count(),
            "controls": self.store.ce_controls.count(),
        }


class ControlledEnvironmentAI:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def optimize(self, *, zone_id: str, temp_c: float = 24.0, humidity_pct: float = 60.0, energy_cost: float = 0.2) -> dict[str, Any]:
        if self.store.ce_zones.get(zone_id) is None:
            raise NotFoundError("zone", zone_id)
        oid = _id("ce_opt")
        growth = round(max(0.0, 1.0 - abs(temp_c - 23) / 15 - abs(humidity_pct - 65) / 50), 3)
        energy = round(max(0.1, energy_cost * (1 + abs(temp_c - 22) / 10)), 3)
        return self.store.ce_ai_opts.save(
            oid,
            {
                "optimization_id": oid,
                "zone_id": zone_id,
                "microclimate_score": growth,
                "growth_optimization": {"target_temp_c": 23.0, "target_humidity_pct": 65.0},
                "energy_optimization": {"estimated_cost": energy, "strategy": "night_setback"},
                "climate_prediction": {"next_6h_temp_c": temp_c + 0.5},
                "alerts": ["humidity_high"] if humidity_pct > 75 else [],
                "resource_optimization": {"water_l": 12.0, "co2_kg": 0.4},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"optimizations": self.store.ce_ai_opts.count()}
