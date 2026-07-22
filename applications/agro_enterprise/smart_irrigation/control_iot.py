"""Smart irrigation control and IoT sensor platform."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

SI_SENSOR_KINDS = [
    "soil_moisture",
    "temperature",
    "humidity",
    "rain",
    "solar_radiation",
    "wind",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SmartIrrigationControl:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def create_zone(self, *, name: str, field_id: str = "", hectares: float = 0.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("zone name required")
        zid = _id("si_zone")
        return self.store.si_zones.save(
            zid,
            {
                "zone_id": zid,
                "name": name,
                "field_id": field_id,
                "hectares": float(hectares),
                "status": "idle",
                "created_at": _now(),
            },
        )

    def schedule(self, *, zone_id: str, starts_at: str, duration_min: int = 30) -> dict[str, Any]:
        if self.store.si_zones.get(zone_id) is None:
            raise NotFoundError("zone", zone_id)
        sid = _id("si_sched")
        return self.store.si_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "zone_id": zone_id,
                "starts_at": starts_at,
                "duration_min": int(duration_min),
                "status": "scheduled",
                "created_at": _now(),
            },
        )

    def set_valve(self, *, zone_id: str, open_valve: bool) -> dict[str, Any]:
        zone = self.store.si_zones.get(zone_id)
        if zone is None:
            raise NotFoundError("zone", zone_id)
        vid = _id("si_valve")
        zone["status"] = "irrigating" if open_valve else "idle"
        self.store.si_zones.save(zone_id, zone)
        return self.store.si_valves.save(
            vid,
            {
                "valve_id": vid,
                "zone_id": zone_id,
                "state": "open" if open_valve else "closed",
                "at": _now(),
            },
        )

    def set_pump(self, *, source_id: str, running: bool, flow_m3h: float = 0.0) -> dict[str, Any]:
        pid = _id("si_pump")
        return self.store.si_pumps.save(
            pid,
            {
                "pump_id": pid,
                "source_id": source_id,
                "running": bool(running),
                "flow_m3h": float(flow_m3h),
                "at": _now(),
            },
        )

    def monitor_flow(self, *, zone_id: str, flow_lpm: float, pressure_bar: float = 2.5) -> dict[str, Any]:
        if self.store.si_zones.get(zone_id) is None:
            raise NotFoundError("zone", zone_id)
        leak = flow_lpm > 0 and pressure_bar < 1.2
        mid = _id("si_flow")
        return self.store.si_flow.save(
            mid,
            {
                "monitor_id": mid,
                "zone_id": zone_id,
                "flow_lpm": float(flow_lpm),
                "pressure_bar": float(pressure_bar),
                "leak_detected": leak,
                "at": _now(),
            },
        )

    def remote_control(self, *, zone_id: str, command: str) -> dict[str, Any]:
        if command not in ("start", "stop", "pause"):
            raise ValidationError("command must be start, stop, or pause")
        if self.store.si_zones.get(zone_id) is None:
            raise NotFoundError("zone", zone_id)
        if command == "start":
            self.set_valve(zone_id=zone_id, open_valve=True)
        elif command == "stop":
            self.set_valve(zone_id=zone_id, open_valve=False)
        cid = _id("si_cmd")
        return self.store.si_remote_commands.save(
            cid,
            {"command_id": cid, "zone_id": zone_id, "command": command, "status": "accepted", "at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {
            "zones": self.store.si_zones.count(),
            "schedules": self.store.si_schedules.count(),
            "valves": self.store.si_valves.count(),
            "leaks": len([f for f in self.store.si_flow.list_all() if f.get("leak_detected")]),
        }


class IrrigationIoT:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.kinds = list(SI_SENSOR_KINDS)

    def register_gateway(self, *, name: str, field_id: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("gateway name required")
        gid = _id("si_gw")
        return self.store.si_gateways.save(
            gid,
            {"gateway_id": gid, "name": name, "field_id": field_id, "status": "online", "created_at": _now()},
        )

    def register_sensor(self, *, kind: str, gateway_id: str, name: str = "") -> dict[str, Any]:
        if kind not in self.kinds:
            raise ValidationError(f"kind must be one of {self.kinds}")
        if self.store.si_gateways.get(gateway_id) is None:
            raise NotFoundError("gateway", gateway_id)
        sid = _id("si_sens")
        return self.store.si_iot_sensors.save(
            sid,
            {
                "sensor_id": sid,
                "kind": kind,
                "gateway_id": gateway_id,
                "name": name or kind,
                "health": "ok",
                "status": "online",
                "created_at": _now(),
            },
        )

    def reading(self, sensor_id: str, *, value: float, unit: str = "") -> dict[str, Any]:
        sensor = self.store.si_iot_sensors.get(sensor_id)
        if sensor is None:
            raise NotFoundError("sensor", sensor_id)
        rid = _id("si_read")
        return self.store.si_iot_readings.save(
            rid,
            {
                "reading_id": rid,
                "sensor_id": sensor_id,
                "kind": sensor["kind"],
                "value": float(value),
                "unit": unit,
                "at": _now(),
            },
        )

    def sensor_health(self) -> dict[str, Any]:
        sensors = self.store.si_iot_sensors.list_all()
        return {
            "total": len(sensors),
            "online": len([s for s in sensors if s.get("status") == "online"]),
            "degraded": len([s for s in sensors if s.get("health") != "ok"]),
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "gateways": self.store.si_gateways.count(),
            "sensors": self.store.si_iot_sensors.count(),
            "readings": self.store.si_iot_readings.count(),
            "kinds": self.kinds,
        }
