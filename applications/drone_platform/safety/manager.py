"""Safety — geofence, no-fly, envelope, altitude/speed/battery/thermal protection (Sprint 11.9)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SafetyManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store
        self._seed_nofly()

    def _seed_nofly(self) -> None:
        if self.store.nofly_zones.list_all():
            return
        for name, south, north, west, east in (
            ("Airport Zone A", 50.40, 50.42, 30.40, 30.45),
            ("Restricted Base", 50.50, 50.51, 30.60, 30.62),
        ):
            zid = f"nfz_{uuid.uuid4().hex[:10]}"
            self.store.nofly_zones.save(
                zid,
                {"zone_id": zid, "name": name, "south": south, "north": north, "west": west, "east": east, "active": True},
            )

    def create_policy(
        self,
        *,
        aircraft_id: str,
        max_alt_m: float = 120,
        max_speed_mps: float = 20,
        min_battery_pct: float = 25,
        max_esc_temp_c: float = 90,
        geofence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not aircraft_id:
            raise ValidationError("aircraft_id required")
        sid = f"saf_{uuid.uuid4().hex[:12]}"
        policy = {
            "safety_id": sid,
            "aircraft_id": aircraft_id,
            "max_alt_m": max_alt_m,
            "max_speed_mps": max_speed_mps,
            "min_battery_pct": min_battery_pct,
            "max_esc_temp_c": max_esc_temp_c,
            "geofence": dict(geofence or {}),
            "violations": [],
            "created_at": _now(),
        }
        self.store.safety_policies.save(sid, policy)
        return policy

    def get_policy(self, safety_id: str) -> dict[str, Any]:
        item = self.store.safety_policies.get(safety_id)
        if item is None:
            raise NotFoundError("safety_policy", safety_id)
        return item

    def set_geofence(self, safety_id: str, *, south: float, north: float, west: float, east: float) -> dict[str, Any]:
        policy = self.get_policy(safety_id)
        if south >= north or west >= east:
            raise ValidationError("invalid geofence bounds")
        policy["geofence"] = {"south": south, "north": north, "west": west, "east": east}
        self.store.safety_policies.save(safety_id, policy)
        return policy

    def list_nofly_zones(self) -> list[dict[str, Any]]:
        self._seed_nofly()
        return self.store.nofly_zones.list_all()

    def add_nofly_zone(self, *, name: str, south: float, north: float, west: float, east: float) -> dict[str, Any]:
        zid = f"nfz_{uuid.uuid4().hex[:10]}"
        zone = {"zone_id": zid, "name": name, "south": south, "north": north, "west": west, "east": east, "active": True}
        self.store.nofly_zones.save(zid, zone)
        return zone

    def _in_box(self, lat: float, lon: float, box: dict[str, Any]) -> bool:
        return float(box["south"]) <= lat <= float(box["north"]) and float(box["west"]) <= lon <= float(box["east"])

    def check_position(self, safety_id: str, *, lat: float, lon: float, alt_m: float = 0, speed_mps: float = 0, battery_pct: float = 100, esc_temp_c: float = 40) -> dict[str, Any]:
        policy = self.get_policy(safety_id)
        violations: list[str] = []
        gf = policy.get("geofence") or {}
        if gf and not self._in_box(lat, lon, gf):
            violations.append("geofence_breach")
        for zone in self.list_nofly_zones():
            if zone.get("active") and self._in_box(lat, lon, zone):
                violations.append(f"nofly:{zone.get('name')}")
        if alt_m > float(policy["max_alt_m"]):
            violations.append("altitude_exceeded")
        if speed_mps > float(policy["max_speed_mps"]):
            violations.append("speed_exceeded")
        if battery_pct < float(policy["min_battery_pct"]):
            violations.append("battery_critical")
        if esc_temp_c > float(policy["max_esc_temp_c"]):
            violations.append("thermal_exceeded")
        policy["violations"] = violations
        self.store.safety_policies.save(safety_id, policy)
        return {
            "safety_id": safety_id,
            "safe": not violations,
            "violations": violations,
            "protections": {
                "geofence": bool(gf),
                "nofly": True,
                "altitude": True,
                "speed": True,
                "battery": True,
                "thermal": True,
                "flight_envelope": True,
            },
        }

    def flight_envelope(self, safety_id: str) -> dict[str, Any]:
        policy = self.get_policy(safety_id)
        return {
            "safety_id": safety_id,
            "envelope": {
                "max_alt_m": policy["max_alt_m"],
                "max_speed_mps": policy["max_speed_mps"],
                "min_battery_pct": policy["min_battery_pct"],
                "max_esc_temp_c": policy["max_esc_temp_c"],
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "safety": "1.0",
            "policies": len(self.store.safety_policies.list_all()),
            "nofly_zones": len(self.list_nofly_zones()),
            "ready": True,
        }


safety_manager = SafetyManager()
