"""Electronics engineering registries and planners (Sprint 11.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


ELECTRONICS_CATALOG: dict[str, list[dict[str, Any]]] = {
    "flight_controller": [
        {"sku": "Pixhawk6C", "mcu": "H7", "imu": "ICM-42688", "outputs": 16},
        {"sku": "CubeOrange+", "mcu": "H7", "imu": "triple", "outputs": 14},
        {"sku": "MatekH743", "mcu": "H7", "imu": "ICM-42688", "outputs": 13},
    ],
    "gps": [
        {"sku": "Here3+", "constellations": "multi", "compass": True},
        {"sku": "M9N", "constellations": "multi", "compass": False},
    ],
    "compass": [
        {"sku": "RM3100", "type": "external"},
        {"sku": "IST8310", "type": "external"},
    ],
    "receiver": [
        {"sku": "ELRS-RX", "protocol": "ELRS", "band": "2.4GHz"},
        {"sku": "R9M", "protocol": "Crossfire", "band": "900MHz"},
        {"sku": "SBUS-RX", "protocol": "SBUS", "band": "2.4GHz"},
    ],
    "telemetry_radio": [
        {"sku": "SiK-915", "band": "915MHz", "rate_kbps": 64},
        {"sku": "RFD900x", "band": "900MHz", "rate_kbps": 250},
    ],
    "vtx": [
        {"sku": "Analog-800mW", "type": "analog_fpv", "power_mw": 800},
        {"sku": "DJI-O3", "type": "digital_fpv", "power_mw": 1200},
        {"sku": "HDZero", "type": "digital_fpv", "power_mw": 500},
    ],
}


class ElectronicsEngineering:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store
        self._seed()

    def _seed(self) -> None:
        if self.store.electronics_parts.count() > 0:
            return
        for category, items in ELECTRONICS_CATALOG.items():
            for item in items:
                eid = f"el_{category}_{item['sku'].lower().replace('+', 'plus').replace('-', '_')}"
                self.store.electronics_parts.save(
                    eid,
                    {"electronics_id": eid, "category": category, **item, "created_at": _now()},
                )

    def registry(self, category: str | None = None) -> list[dict[str, Any]]:
        items = self.store.electronics_parts.list_all()
        if category:
            return [i for i in items if i.get("category") == category]
        return items

    def flight_controller_registry(self) -> list[dict[str, Any]]:
        return self.registry("flight_controller")

    def gps_registry(self) -> list[dict[str, Any]]:
        return self.registry("gps")

    def compass_registry(self) -> list[dict[str, Any]]:
        return self.registry("compass")

    def receiver_registry(self) -> list[dict[str, Any]]:
        return self.registry("receiver")

    def elrs_support(self) -> dict[str, Any]:
        return {"protocol": "ELRS", "supported": True, "receivers": [r for r in self.receiver_registry() if r.get("protocol") == "ELRS"]}

    def crossfire_support(self) -> dict[str, Any]:
        return {"protocol": "Crossfire", "supported": True, "receivers": [r for r in self.receiver_registry() if r.get("protocol") == "Crossfire"]}

    def telemetry_radios(self) -> list[dict[str, Any]]:
        return self.registry("telemetry_radio")

    def video_transmitters(self) -> list[dict[str, Any]]:
        return self.registry("vtx")

    def analog_fpv(self) -> list[dict[str, Any]]:
        return [v for v in self.video_transmitters() if v.get("type") == "analog_fpv"]

    def digital_fpv(self) -> list[dict[str, Any]]:
        return [v for v in self.video_transmitters() if v.get("type") == "digital_fpv"]

    def power_distribution(self, *, battery_v: float, loads: list[dict[str, Any]]) -> dict[str, Any]:
        total_a = sum(float(l.get("amps", 0)) for l in loads)
        return {
            "battery_v": battery_v,
            "loads": loads,
            "total_current_a": round(total_a, 2),
            "total_power_w": round(battery_v * total_a, 2),
            "pdb_recommendation": "60A PDB" if total_a < 50 else "120A PDB / dual path",
        }

    def bec_calculator(self, *, input_v: float, output_v: float, load_a: float, efficiency: float = 0.85) -> dict[str, Any]:
        if efficiency <= 0 or efficiency > 1:
            raise ValidationError("efficiency must be in (0,1]")
        input_a = (output_v * load_a) / (input_v * efficiency)
        return {
            "input_v": input_v,
            "output_v": output_v,
            "load_a": load_a,
            "efficiency": efficiency,
            "input_current_a": round(input_a, 3),
            "heat_w": round(output_v * load_a * (1 - efficiency) / max(efficiency, 1e-9) * efficiency, 2),
        }

    def wiring_planner(self, *, harness: list[dict[str, Any]]) -> dict[str, Any]:
        awg_map = {10: 5.26, 12: 3.31, 14: 2.08, 16: 1.31, 18: 0.823, 20: 0.518, 22: 0.326}
        lines = []
        for h in harness:
            amps = float(h.get("amps", 1))
            # pick minimal AWG that can carry ~amps (very rough)
            chosen = 22
            for awg, area in sorted(awg_map.items()):
                if area >= amps * 0.1:
                    chosen = awg
                    break
            lines.append({**h, "recommended_awg": chosen})
        return {"harness": lines, "count": len(lines)}

    def status(self) -> dict[str, Any]:
        return {
            "electronics_engineering": "1.0",
            "parts": self.store.electronics_parts.count(),
            "categories": sorted({p.get("category") for p in self.registry()}),
            "capabilities": [
                "flight_controller_registry",
                "gps_registry",
                "compass_registry",
                "receiver_registry",
                "elrs",
                "crossfire",
                "telemetry_radios",
                "vtx",
                "analog_fpv",
                "digital_fpv",
                "power_distribution",
                "bec_calculator",
                "wiring_planner",
            ],
        }


electronics_engineering = ElectronicsEngineering()
