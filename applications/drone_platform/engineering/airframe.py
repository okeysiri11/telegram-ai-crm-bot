"""Airframe engineering — frames, wings, CG, structural validation (Sprint 11.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


FRAME_TYPES = ("multirotor", "fixed_wing", "flying_wing", "vtol", "helicopter", "custom")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Seed catalog of common frame families
FRAME_DATABASE: list[dict[str, Any]] = [
    {"sku": "QR-X450", "name": "Quad X 450", "frame_type": "multirotor", "wheelbase_mm": 450, "arms": 4},
    {"sku": "HEX-650", "name": "Hex 650", "frame_type": "multirotor", "wheelbase_mm": 650, "arms": 6},
    {"sku": "FW-1.8M", "name": "Trainer 1.8m", "frame_type": "fixed_wing", "span_m": 1.8, "chord_m": 0.25},
    {"sku": "FWING-1.2", "name": "Flying Wing 1.2m", "frame_type": "flying_wing", "span_m": 1.2, "sweep_deg": 30},
    {"sku": "VTOL-QUADPLANE", "name": "QuadPlane VTOL", "frame_type": "vtol", "span_m": 2.0, "lift_motors": 4},
]


class AirframeManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def frame_database(self) -> list[dict[str, Any]]:
        return list(FRAME_DATABASE)

    def create(
        self,
        *,
        name: str,
        frame_type: str,
        specs: dict[str, Any] | None = None,
        masses: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        frame_type = frame_type.lower().strip()
        if frame_type not in FRAME_TYPES:
            raise ValidationError(f"Unsupported frame type: {frame_type}")
        aid = f"af_{uuid.uuid4().hex[:12]}"
        item = {
            "airframe_id": aid,
            "name": name,
            "frame_type": frame_type,
            "specs": dict(specs or {}),
            "masses": dict(masses or {}),
            "created_at": _now(),
        }
        self.store.airframes.save(aid, item)
        return item

    def get(self, airframe_id: str) -> dict[str, Any]:
        item = self.store.airframes.get(airframe_id)
        if item is None:
            raise NotFoundError("airframe", airframe_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.airframes.list_all()

    def wing_calculator(self, *, span_m: float, chord_m: float, airfoil_cl: float = 1.2, density: float = 1.225) -> dict[str, Any]:
        area = span_m * chord_m
        aspect = span_m / max(chord_m, 1e-6)
        # lift at 12 m/s cruise estimate
        v = 12.0
        lift_n = 0.5 * density * v * v * area * airfoil_cl
        result = {
            "span_m": span_m,
            "chord_m": chord_m,
            "wing_area_m2": round(area, 4),
            "aspect_ratio": round(aspect, 3),
            "est_lift_n_at_12mps": round(lift_n, 2),
            "est_lift_kgf": round(lift_n / 9.81, 3),
        }
        self._calc("wing", result)
        return result

    def flying_wing_designer(self, *, span_m: float, root_chord_m: float, tip_chord_m: float, sweep_deg: float = 30.0) -> dict[str, Any]:
        area = span_m * (root_chord_m + tip_chord_m) / 2
        taper = tip_chord_m / max(root_chord_m, 1e-6)
        result = {
            "design": "flying_wing",
            "span_m": span_m,
            "root_chord_m": root_chord_m,
            "tip_chord_m": tip_chord_m,
            "sweep_deg": sweep_deg,
            "taper_ratio": round(taper, 3),
            "wing_area_m2": round(area, 4),
            "notes": ["Balance elevon authority", "Check CG vs MAC"],
        }
        return self.create(name=f"FlyingWing-{span_m}m", frame_type="flying_wing", specs=result)

    def multirotor_designer(self, *, arms: int = 4, wheelbase_mm: float = 450, auw_kg: float = 1.5) -> dict[str, Any]:
        if arms < 3:
            raise ValidationError("multirotor needs >= 3 arms")
        thrust_per_motor_kgf = (auw_kg * 2.0) / arms  # 2:1 hover thrust ratio target
        result = {
            "design": "multirotor",
            "arms": arms,
            "wheelbase_mm": wheelbase_mm,
            "auw_kg": auw_kg,
            "target_thrust_per_motor_kgf": round(thrust_per_motor_kgf, 3),
            "layout": "X" if arms == 4 else f"{arms}-motor",
        }
        return self.create(name=f"Multi-{arms}x{int(wheelbase_mm)}", frame_type="multirotor", specs=result, masses={"auw_kg": auw_kg})

    def vtol_designer(self, *, span_m: float, lift_motors: int = 4, cruise_motor: int = 1, auw_kg: float = 5.0) -> dict[str, Any]:
        result = {
            "design": "vtol",
            "span_m": span_m,
            "lift_motors": lift_motors,
            "cruise_motor": cruise_motor,
            "auw_kg": auw_kg,
            "transition_notes": ["Validate Q_ASSIST", "Separate lift/cruise power paths"],
        }
        return self.create(name=f"VTOL-{span_m}m", frame_type="vtol", specs=result, masses={"auw_kg": auw_kg})

    def payload_calculator(self, *, empty_kg: float, max_takeoff_kg: float, reserve_kg: float = 0.1) -> dict[str, Any]:
        payload = max(0.0, max_takeoff_kg - empty_kg - reserve_kg)
        result = {
            "empty_kg": empty_kg,
            "max_takeoff_kg": max_takeoff_kg,
            "reserve_kg": reserve_kg,
            "max_payload_kg": round(payload, 3),
            "payload_fraction": round(payload / max(max_takeoff_kg, 1e-6), 3),
        }
        self._calc("payload", result)
        return result

    def cg_calculator(self, *, stations: list[dict[str, float]], reference_mm: float = 0.0) -> dict[str, Any]:
        if not stations:
            raise ValidationError("stations required")
        moment = 0.0
        mass = 0.0
        for s in stations:
            m = float(s.get("mass_kg", 0))
            x = float(s.get("x_mm", 0)) - reference_mm
            moment += m * x
            mass += m
        cg = moment / max(mass, 1e-9)
        result = {"total_mass_kg": round(mass, 4), "cg_mm": round(cg, 2), "reference_mm": reference_mm, "stations": stations}
        self._calc("cg", result)
        return result

    def weight_distribution(self, *, masses: dict[str, float]) -> dict[str, Any]:
        total = sum(float(v) for v in masses.values())
        dist = {k: round(float(v) / max(total, 1e-9), 4) for k, v in masses.items()}
        result = {"total_kg": round(total, 4), "distribution": dist, "heaviest": max(dist, key=dist.get) if dist else None}
        self._calc("weight_distribution", result)
        return result

    def structural_validator(self, *, auw_kg: float, material_sf: float = 1.5, max_load_factor: float = 3.0) -> dict[str, Any]:
        design_load = auw_kg * max_load_factor * material_sf
        ok = design_load < auw_kg * 8  # simplistic envelope
        result = {
            "auw_kg": auw_kg,
            "material_sf": material_sf,
            "max_load_factor": max_load_factor,
            "design_load_kgf": round(design_load, 2),
            "valid": ok,
            "issues": [] if ok else ["Design load exceeds simple envelope — review structure"],
        }
        self._calc("structural", result)
        return result

    def _calc(self, kind: str, result: dict[str, Any]) -> None:
        cid = f"calc_{uuid.uuid4().hex[:10]}"
        self.store.eng_calculations.save(cid, {"calculation_id": cid, "kind": kind, "result": result, "at": _now()})

    def status(self) -> dict[str, Any]:
        return {
            "airframe_engineering": "1.0",
            "frame_types": list(FRAME_TYPES),
            "catalog_count": len(FRAME_DATABASE),
            "airframe_count": self.store.airframes.count(),
            "capabilities": [
                "airframe_manager",
                "frame_database",
                "wing_calculator",
                "flying_wing_designer",
                "multirotor_designer",
                "vtol_designer",
                "payload_calculator",
                "cg_calculator",
                "weight_distribution",
                "structural_validator",
            ],
        }


airframe_manager = AirframeManager()
