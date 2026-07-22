"""System health monitoring — sensors, power, motors, ESC, battery, storage, CPU/RAM (Sprint 11.9)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SystemHealthMonitor:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def open(self, *, aircraft_id: str) -> dict[str, Any]:
        if not aircraft_id:
            raise ValidationError("aircraft_id required")
        hid = f"hlth_{uuid.uuid4().hex[:12]}"
        snap = {
            "health_id": hid,
            "aircraft_id": aircraft_id,
            "sensors": {"imu": "ok", "baro": "ok", "mag": "ok", "gps": "ok"},
            "power": {"rail_5v": "ok", "rail_12v": "ok", "voltage_v": 16.2},
            "motors": {"m1": "ok", "m2": "ok", "m3": "ok", "m4": "ok"},
            "esc": {"temp_c": 45, "status": "ok"},
            "battery": {"pct": 85, "soh": 0.96, "status": "ok"},
            "storage": {"free_mb": 2048, "status": "ok"},
            "cpu_ram": {"cpu_pct": 35, "ram_pct": 48, "status": "ok"},
            "overall": "healthy",
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.health_snapshots.save(hid, snap)
        return snap

    def get(self, health_id: str) -> dict[str, Any]:
        item = self.store.health_snapshots.get(health_id)
        if item is None:
            raise NotFoundError("health_snapshot", health_id)
        return item

    def _recompute(self, snap: dict[str, Any]) -> str:
        bad = []
        for group in ("sensors", "motors"):
            for k, v in snap.get(group, {}).items():
                if v != "ok":
                    bad.append(f"{group}.{k}")
        if snap.get("power", {}).get("rail_5v") != "ok" or snap.get("power", {}).get("rail_12v") != "ok":
            bad.append("power")
        if snap.get("esc", {}).get("status") != "ok" or float(snap.get("esc", {}).get("temp_c", 0)) > 85:
            bad.append("esc")
        if snap.get("battery", {}).get("status") != "ok" or float(snap.get("battery", {}).get("pct", 100)) < 20:
            bad.append("battery")
        if snap.get("storage", {}).get("status") != "ok":
            bad.append("storage")
        if snap.get("cpu_ram", {}).get("status") != "ok" or float(snap.get("cpu_ram", {}).get("cpu_pct", 0)) > 90:
            bad.append("cpu_ram")
        snap["issues"] = bad
        return "critical" if len(bad) >= 3 else "degraded" if bad else "healthy"

    def update(self, health_id: str, *, section: str, values: dict[str, Any]) -> dict[str, Any]:
        snap = self.get(health_id)
        if section not in snap:
            raise ValidationError(f"unknown health section: {section}")
        if isinstance(snap[section], dict):
            snap[section] = {**snap[section], **values}
        else:
            snap[section] = values
        snap["overall"] = self._recompute(snap)
        snap["updated_at"] = _now()
        self.store.health_snapshots.save(health_id, snap)
        return snap

    def sensor_health(self, health_id: str) -> dict[str, Any]:
        return {"health_id": health_id, "sensors": self.get(health_id)["sensors"]}

    def power_health(self, health_id: str) -> dict[str, Any]:
        return {"health_id": health_id, "power": self.get(health_id)["power"]}

    def motor_health(self, health_id: str) -> dict[str, Any]:
        return {"health_id": health_id, "motors": self.get(health_id)["motors"]}

    def esc_health(self, health_id: str) -> dict[str, Any]:
        return {"health_id": health_id, "esc": self.get(health_id)["esc"]}

    def battery_health(self, health_id: str) -> dict[str, Any]:
        return {"health_id": health_id, "battery": self.get(health_id)["battery"]}

    def storage_health(self, health_id: str) -> dict[str, Any]:
        return {"health_id": health_id, "storage": self.get(health_id)["storage"]}

    def cpu_ram_monitor(self, health_id: str) -> dict[str, Any]:
        return {"health_id": health_id, "cpu_ram": self.get(health_id)["cpu_ram"]}

    def overview(self, health_id: str) -> dict[str, Any]:
        snap = self.get(health_id)
        snap["overall"] = self._recompute(snap)
        self.store.health_snapshots.save(health_id, snap)
        return {
            "health_id": health_id,
            "overall": snap["overall"],
            "issues": snap.get("issues", []),
            "aircraft_id": snap["aircraft_id"],
        }

    def status(self) -> dict[str, Any]:
        return {"health_monitoring": "1.0", "snapshots": len(self.store.health_snapshots.list_all()), "ready": True}


system_health_monitor = SystemHealthMonitor()
