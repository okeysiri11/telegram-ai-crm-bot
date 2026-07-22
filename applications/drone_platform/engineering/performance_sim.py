"""Engineering performance simulation (Sprint 11.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EngineeringPerformanceSimulator:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def _save(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        sid = f"esim_{uuid.uuid4().hex[:12]}"
        item = {"simulation_id": sid, "kind": kind, "created_at": _now(), **payload}
        self.store.eng_simulations.save(sid, item)
        return item

    def flight_performance(self, *, auw_kg: float, thrust_kgf: float, drag_n: float = 5.0) -> dict[str, Any]:
        twr = thrust_kgf / max(auw_kg, 1e-9)
        climb = max(0.0, (thrust_kgf * 9.81 - auw_kg * 9.81 - drag_n) / max(auw_kg, 1e-9))
        return self._save(
            "flight_performance",
            {"auw_kg": auw_kg, "thrust_kgf": thrust_kgf, "twr": round(twr, 3), "est_climb_mps": round(climb, 2), "drag_n": drag_n},
        )

    def power_simulator(self, *, voltage: float, hover_a: float, cruise_a: float, hover_min: float, cruise_min: float) -> dict[str, Any]:
        energy_wh = voltage * ((hover_a * hover_min + cruise_a * cruise_min) / 60.0)
        return self._save(
            "power",
            {
                "voltage": voltage,
                "hover_a": hover_a,
                "cruise_a": cruise_a,
                "hover_min": hover_min,
                "cruise_min": cruise_min,
                "energy_wh": round(energy_wh, 2),
            },
        )

    def range_simulator(self, *, cruise_speed_mps: float, cruise_min: float, reserve_min: float = 5.0) -> dict[str, Any]:
        usable = max(0.0, cruise_min - reserve_min)
        distance_m = cruise_speed_mps * usable * 60
        return self._save(
            "range",
            {
                "cruise_speed_mps": cruise_speed_mps,
                "cruise_min": cruise_min,
                "reserve_min": reserve_min,
                "range_m": round(distance_m, 1),
                "range_km": round(distance_m / 1000.0, 3),
            },
        )

    def payload_simulator(self, *, empty_kg: float, max_takeoff_kg: float, battery_kg: float) -> dict[str, Any]:
        payload = max(0.0, max_takeoff_kg - empty_kg - battery_kg)
        return self._save(
            "payload",
            {"empty_kg": empty_kg, "battery_kg": battery_kg, "max_takeoff_kg": max_takeoff_kg, "payload_kg": round(payload, 3)},
        )

    def weather_impact(self, *, base_range_km: float, wind_mps: float, rain: bool = False) -> dict[str, Any]:
        factor = 1.0 - min(0.4, wind_mps / 40.0) - (0.15 if rain else 0)
        return self._save(
            "weather",
            {
                "base_range_km": base_range_km,
                "wind_mps": wind_mps,
                "rain": rain,
                "adjusted_range_km": round(base_range_km * max(factor, 0.4), 3),
                "factor": round(factor, 3),
            },
        )

    def wind_resistance(self, *, frontal_area_m2: float, wind_mps: float, cd: float = 0.8, density: float = 1.225) -> dict[str, Any]:
        force = 0.5 * density * cd * frontal_area_m2 * wind_mps * wind_mps
        return self._save("wind", {"frontal_area_m2": frontal_area_m2, "wind_mps": wind_mps, "drag_n": round(force, 2)})

    def temperature_effects(self, *, capacity_mah: float, temp_c: float) -> dict[str, Any]:
        # cold reduces usable capacity roughly
        factor = 1.0 if temp_c >= 20 else max(0.7, 1.0 - (20 - temp_c) * 0.01)
        return self._save(
            "temperature",
            {"temp_c": temp_c, "rated_mah": capacity_mah, "effective_mah": round(capacity_mah * factor, 1), "factor": round(factor, 3)},
        )

    def altitude_effects(self, *, sea_level_thrust_kgf: float, altitude_m: float) -> dict[str, Any]:
        # density ratio approx
        factor = max(0.5, 1.0 - altitude_m / 20000.0)
        return self._save(
            "altitude",
            {
                "altitude_m": altitude_m,
                "sea_level_thrust_kgf": sea_level_thrust_kgf,
                "thrust_kgf": round(sea_level_thrust_kgf * factor, 3),
                "density_factor": round(factor, 3),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "engineering_simulation": "1.0",
            "run_count": self.store.eng_simulations.count(),
            "capabilities": [
                "flight_performance",
                "power",
                "range",
                "payload",
                "weather",
                "wind",
                "temperature",
                "altitude",
            ],
        }


engineering_performance_simulator = EngineeringPerformanceSimulator()
