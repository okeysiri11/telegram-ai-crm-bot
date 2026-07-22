"""Propulsion calculators — motors, props, ESC, thrust/power (Sprint 11.5)."""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


MOTOR_DATABASE: list[dict[str, Any]] = [
    {"sku": "MN4014-400", "kv": 400, "max_amps": 30, "weight_g": 165, "shaft_mm": 5},
    {"sku": "MN5008-340", "kv": 340, "max_amps": 35, "weight_g": 195, "shaft_mm": 6},
    {"sku": "2212-920", "kv": 920, "max_amps": 18, "weight_g": 55, "shaft_mm": 3.17},
    {"sku": "2806-1300", "kv": 1300, "max_amps": 30, "weight_g": 48, "shaft_mm": 5},
]

PROPELLER_DATABASE: list[dict[str, Any]] = [
    {"sku": "APC-10x4.7", "diameter_in": 10, "pitch_in": 4.7, "blades": 2},
    {"sku": "APC-15x5.5", "diameter_in": 15, "pitch_in": 5.5, "blades": 2},
    {"sku": "T-Motor-18x6.1", "diameter_in": 18, "pitch_in": 6.1, "blades": 2},
    {"sku": "HQ-5x4.3x3", "diameter_in": 5, "pitch_in": 4.3, "blades": 3},
]

ESC_DATABASE: list[dict[str, Any]] = [
    {"sku": "BLHeli-30A", "amps_cont": 30, "amps_burst": 40, "lipo_s": "2-4S", "protocol": "DShot"},
    {"sku": "FOC-60A", "amps_cont": 60, "amps_burst": 80, "lipo_s": "4-6S", "protocol": "CAN"},
    {"sku": "Hobbywing-XRotor-40", "amps_cont": 40, "amps_burst": 60, "lipo_s": "3-6S", "protocol": "PWM"},
]


class PropulsionCalculator:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store
        self._seed()

    def _seed(self) -> None:
        if self.store.motors.count() == 0:
            for m in MOTOR_DATABASE:
                mid = f"mot_{m['sku'].lower().replace('-', '_')}"
                self.store.motors.save(mid, {"motor_id": mid, **m})
        if self.store.propellers.count() == 0:
            for p in PROPELLER_DATABASE:
                pid = f"prop_{p['sku'].lower().replace('-', '_').replace('.', '_')}"
                self.store.propellers.save(pid, {"propeller_id": pid, **p})
        if self.store.escs.count() == 0:
            for e in ESC_DATABASE:
                eid = f"esc_{e['sku'].lower().replace('-', '_')}"
                self.store.escs.save(eid, {"esc_id": eid, **e})

    def motor_database(self) -> list[dict[str, Any]]:
        return self.store.motors.list_all()

    def propeller_database(self) -> list[dict[str, Any]]:
        return self.store.propellers.list_all()

    def esc_database(self) -> list[dict[str, Any]]:
        return self.store.escs.list_all()

    def gear_ratio(self, *, motor_rpm: float, prop_rpm: float) -> dict[str, Any]:
        if prop_rpm <= 0:
            raise ValidationError("prop_rpm must be > 0")
        ratio = motor_rpm / prop_rpm
        return {"motor_rpm": motor_rpm, "prop_rpm": prop_rpm, "gear_ratio": round(ratio, 3), "reduction": ratio > 1}

    def thrust_calculator(
        self,
        *,
        diameter_in: float,
        pitch_in: float,
        rpm: float,
        air_density: float = 1.225,
    ) -> dict[str, Any]:
        # Simplified momentum/static thrust estimate (engineering approximation)
        d_m = diameter_in * 0.0254
        pitch_m = pitch_in * 0.0254
        tip_speed = math.pi * d_m * (rpm / 60.0)
        thrust_n = 0.5 * air_density * (math.pi * (d_m / 2) ** 2) * (rpm / 60.0 * pitch_m) ** 2 * 0.6
        return {
            "diameter_in": diameter_in,
            "pitch_in": pitch_in,
            "rpm": rpm,
            "tip_speed_mps": round(tip_speed, 2),
            "thrust_n": round(thrust_n, 2),
            "thrust_kgf": round(thrust_n / 9.81, 3),
        }

    def hover_calculator(self, *, auw_kg: float, motors: int, thrust_per_motor_kgf: float) -> dict[str, Any]:
        total = motors * thrust_per_motor_kgf
        ratio = total / max(auw_kg, 1e-9)
        return {
            "auw_kg": auw_kg,
            "motors": motors,
            "total_thrust_kgf": round(total, 3),
            "thrust_to_weight": round(ratio, 3),
            "hover_ok": ratio >= 1.8,
            "hover_throttle_est": round(min(0.95, 1.0 / max(ratio, 1e-9)), 3),
        }

    def cruise_calculator(self, *, thrust_n: float, drag_n: float, speed_mps: float) -> dict[str, Any]:
        excess = thrust_n - drag_n
        return {
            "thrust_n": thrust_n,
            "drag_n": drag_n,
            "speed_mps": speed_mps,
            "excess_thrust_n": round(excess, 2),
            "cruise_capable": excess >= 0,
            "power_est_w": round(max(thrust_n, 0) * speed_mps, 1),
        }

    def max_speed_estimator(self, *, power_w: float, drag_coeff: float = 0.5, area_m2: float = 0.05, density: float = 1.225) -> dict[str, Any]:
        # P ≈ 0.5 * rho * Cd * A * V^3
        denom = 0.5 * density * drag_coeff * area_m2
        v = (power_w / max(denom, 1e-9)) ** (1 / 3)
        return {"power_w": power_w, "max_speed_mps": round(v, 2), "max_speed_kmh": round(v * 3.6, 1)}

    def power_consumption(self, *, voltage: float, current_a: float, motors: int = 1, duty: float = 1.0) -> dict[str, Any]:
        power = voltage * current_a * motors * duty
        return {"voltage": voltage, "current_a": current_a, "motors": motors, "duty": duty, "power_w": round(power, 2)}

    def efficiency_optimizer(self, *, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        if not candidates:
            raise ValidationError("candidates required")
        scored = []
        for c in candidates:
            thrust = float(c.get("thrust_kgf", 0))
            power = float(c.get("power_w", 1))
            score = thrust / max(power, 1e-9) * 1000
            scored.append({**c, "efficiency_score": round(score, 3)})
        scored.sort(key=lambda x: x["efficiency_score"], reverse=True)
        return {"ranked": scored, "best": scored[0]}

    def status(self) -> dict[str, Any]:
        return {
            "propulsion_calculator": "1.0",
            "motors": self.store.motors.count(),
            "propellers": self.store.propellers.count(),
            "escs": self.store.escs.count(),
            "capabilities": [
                "motor_database",
                "propeller_database",
                "esc_database",
                "gear_ratio",
                "thrust",
                "hover",
                "cruise",
                "max_speed",
                "power_consumption",
                "efficiency_optimizer",
            ],
        }


propulsion_calculator = PropulsionCalculator()
