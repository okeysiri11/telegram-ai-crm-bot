"""Remote vehicle management and predictive AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

COMMANDS = ["lock", "unlock", "honk", "locate", "immobilize", "diagnostics_pull"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RemoteVehicleManagement:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def health(self, connected_vehicle_id: str) -> dict[str, Any]:
        vehicle = self.store.cc_vehicles.get(connected_vehicle_id)
        if vehicle is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        obd = [o for o in self.store.cc_obd.list_all() if o.get("connected_vehicle_id") == connected_vehicle_id]
        batt = [b for b in self.store.cc_battery.list_all() if b.get("connected_vehicle_id") == connected_vehicle_id]
        score = 90.0
        if obd and not obd[-1].get("engine_ok"):
            score -= 25
        if batt and float(batt[-1].get("soc_pct") or 100) < 30:
            score -= 15
        hid = _id("cc_health")
        result = {
            "health_id": hid,
            "connected_vehicle_id": connected_vehicle_id,
            "vin": vehicle["vin"],
            "health_score": round(score, 1),
            "status": "critical" if score < 60 else "watch" if score < 80 else "ok",
            "at": _now(),
        }
        return self.store.cc_health.save(hid, result)

    def remote_diagnostics(self, connected_vehicle_id: str) -> dict[str, Any]:
        vehicle = self.store.cc_vehicles.get(connected_vehicle_id)
        if vehicle is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        did = _id("cc_diag")
        result = {
            "diagnostics_id": did,
            "connected_vehicle_id": connected_vehicle_id,
            "vin": vehicle["vin"],
            "systems": {"engine": "ok", "brakes": "ok", "battery": "ok", "tires": "ok"},
            "at": _now(),
        }
        return self.store.cc_diagnostics.save(did, result)

    def notify(self, *, connected_vehicle_id: str, title: str, body: str = "") -> dict[str, Any]:
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        nid = _id("cc_ntf")
        note = {
            "notification_id": nid,
            "connected_vehicle_id": connected_vehicle_id,
            "title": title,
            "body": body,
            "at": _now(),
        }
        return self.store.cc_notifications.save(nid, note)

    def command(self, *, connected_vehicle_id: str, command: str) -> dict[str, Any]:
        if command not in COMMANDS:
            raise ValidationError(f"command must be one of {COMMANDS}")
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        cid = _id("cc_cmd")
        record = {
            "command_id": cid,
            "connected_vehicle_id": connected_vehicle_id,
            "command": command,
            "status": "accepted",
            "at": _now(),
        }
        return self.store.cc_commands.save(cid, record)

    def maintenance_alert(self, *, connected_vehicle_id: str, message: str, due_at: str = "") -> dict[str, Any]:
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        aid = _id("cc_alert")
        alert = {
            "alert_id": aid,
            "connected_vehicle_id": connected_vehicle_id,
            "message": message,
            "due_at": due_at,
            "status": "open",
            "at": _now(),
        }
        return self.store.cc_maintenance_alerts.save(aid, alert)

    def register_firmware(self, *, connected_vehicle_id: str, component: str, version: str) -> dict[str, Any]:
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        fid = _id("cc_fw")
        record = {
            "firmware_id": fid,
            "connected_vehicle_id": connected_vehicle_id,
            "component": component,
            "version": version,
            "status": "current",
            "registered_at": _now(),
        }
        self.store.cc_firmware.save(fid, record)
        self.store.cc_software_registry.save(
            f"{connected_vehicle_id}:{component}",
            {"connected_vehicle_id": connected_vehicle_id, "component": component, "version": version, "at": _now()},
        )
        return record

    def status(self) -> dict[str, Any]:
        return {
            "health_checks": self.store.cc_health.count(),
            "diagnostics": self.store.cc_diagnostics.count(),
            "commands": self.store.cc_commands.count(),
            "alerts": self.store.cc_maintenance_alerts.count(),
        }


class PredictiveAI:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def predict(
        self,
        *,
        connected_vehicle_id: str,
        mileage: int = 50000,
        battery_soc: float = 80.0,
        engine_load: float = 0.4,
        brake_km: float = 20000.0,
        tire_km: float = 25000.0,
        utilization: float = 0.5,
    ) -> dict[str, Any]:
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        fail = min(0.95, 0.08 + mileage / 250000 + engine_load * 0.2)
        batt_life = max(0.1, round(battery_soc / 100 * (1 - mileage / 300000), 3))
        engine = max(0.05, round(1 - engine_load * 0.4 - mileage / 400000, 3))
        brake = max(0.05, round(1 - brake_km / 60000, 3))
        tire = max(0.05, round(1 - tire_km / 50000, 3))
        schedule = []
        if fail > 0.35:
            schedule.append("diagnostic_service")
        if brake < 0.4:
            schedule.append("brake_service")
        if tire < 0.35:
            schedule.append("tire_rotation")
        if batt_life < 0.4:
            schedule.append("battery_check")
        pid = _id("cc_pred")
        result = {
            "prediction_id": pid,
            "connected_vehicle_id": connected_vehicle_id,
            "failure_probability": round(fail, 3),
            "battery_life_prediction": batt_life,
            "engine_health_prediction": engine,
            "brake_wear_prediction": brake,
            "tire_wear_prediction": tire,
            "maintenance_scheduling": schedule or ["routine_interval"],
            "vehicle_utilization_analysis": {"utilization": utilization, "band": "high" if utilization > 0.7 else "normal"},
            "at": _now(),
        }
        return self.store.cc_predictions.save(pid, result)

    def status(self) -> dict[str, Any]:
        return {"predictions": self.store.cc_predictions.count()}
