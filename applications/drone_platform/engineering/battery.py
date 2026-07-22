"""Battery engineering — pack builder, chemistry calculators (Sprint 11.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


CELL_PROFILES = {
    "18650": {"nominal_v": 3.6, "full_v": 4.2, "capacity_mah_default": 3000, "chemistry": "li-ion"},
    "21700": {"nominal_v": 3.6, "full_v": 4.2, "capacity_mah_default": 4800, "chemistry": "li-ion"},
    "lipo": {"nominal_v": 3.7, "full_v": 4.2, "capacity_mah_default": 5000, "chemistry": "lipo"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BatteryEngineering:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def build_pack(
        self,
        *,
        name: str,
        cell_type: str,
        series: int,
        parallel: int,
        cell_capacity_mah: float | None = None,
        cell_ir_mohm: float = 20.0,
    ) -> dict[str, Any]:
        cell_type = cell_type.lower().strip()
        if cell_type not in CELL_PROFILES:
            raise ValidationError(f"Unsupported cell type: {cell_type}")
        if series < 1 or parallel < 1:
            raise ValidationError("series and parallel must be >= 1")
        profile = CELL_PROFILES[cell_type]
        cap = float(cell_capacity_mah if cell_capacity_mah is not None else profile["capacity_mah_default"])
        pack = {
            "pack_id": f"bat_{uuid.uuid4().hex[:12]}",
            "name": name,
            "cell_type": cell_type,
            "chemistry": profile["chemistry"],
            "series": series,
            "parallel": parallel,
            "cell_count": series * parallel,
            "configuration": f"{series}S{parallel}P",
            "capacity_mah": cap * parallel,
            "nominal_voltage": round(profile["nominal_v"] * series, 2),
            "full_voltage": round(profile["full_v"] * series, 2),
            "energy_wh": round((cap * parallel / 1000.0) * profile["nominal_v"] * series, 2),
            "pack_ir_mohm": round(cell_ir_mohm * series / parallel, 2),
            "created_at": _now(),
        }
        self.store.battery_packs.save(pack["pack_id"], pack)
        return pack

    def support_18650(self, *, series: int, parallel: int, capacity_mah: float = 3000) -> dict[str, Any]:
        return self.build_pack(name="18650 Pack", cell_type="18650", series=series, parallel=parallel, cell_capacity_mah=capacity_mah)

    def support_21700(self, *, series: int, parallel: int, capacity_mah: float = 4800) -> dict[str, Any]:
        return self.build_pack(name="21700 Pack", cell_type="21700", series=series, parallel=parallel, cell_capacity_mah=capacity_mah)

    def li_ion_calculator(self, *, series: int, parallel: int, cell_mah: float = 3000) -> dict[str, Any]:
        return self.build_pack(name="Li-Ion Calc", cell_type="18650", series=series, parallel=parallel, cell_capacity_mah=cell_mah)

    def lipo_calculator(self, *, series: int, capacity_mah: float, c_rating: float = 25.0) -> dict[str, Any]:
        pack = self.build_pack(name="LiPo Calc", cell_type="lipo", series=series, parallel=1, cell_capacity_mah=capacity_mah)
        pack["c_rating"] = c_rating
        pack["max_continuous_a"] = round((capacity_mah / 1000.0) * c_rating, 2)
        self.store.battery_packs.save(pack["pack_id"], pack)
        return pack

    def series_parallel_builder(self, *, cell_type: str, series: int, parallel: int, cell_mah: float) -> dict[str, Any]:
        return self.build_pack(name=f"{series}S{parallel}P", cell_type=cell_type, series=series, parallel=parallel, cell_capacity_mah=cell_mah)

    def capacity_calculator(self, *, cell_mah: float, parallel: int) -> dict[str, Any]:
        return {"cell_mah": cell_mah, "parallel": parallel, "pack_capacity_mah": cell_mah * parallel}

    def voltage_calculator(self, *, cell_nominal_v: float, series: int) -> dict[str, Any]:
        return {
            "series": series,
            "nominal_v": round(cell_nominal_v * series, 2),
            "full_v": round(4.2 * series, 2),
            "storage_v": round(3.8 * series, 2),
            "empty_v": round(3.3 * series, 2),
        }

    def internal_resistance(self, *, cell_ir_mohm: float, series: int, parallel: int) -> dict[str, Any]:
        pack_ir = cell_ir_mohm * series / max(parallel, 1)
        return {"cell_ir_mohm": cell_ir_mohm, "series": series, "parallel": parallel, "pack_ir_mohm": round(pack_ir, 2)}

    def flight_time_estimator(self, *, capacity_mah: float, average_current_a: float, usable_fraction: float = 0.8) -> dict[str, Any]:
        if average_current_a <= 0:
            raise ValidationError("average_current_a must be > 0")
        hours = (capacity_mah / 1000.0) * usable_fraction / average_current_a
        return {
            "capacity_mah": capacity_mah,
            "average_current_a": average_current_a,
            "usable_fraction": usable_fraction,
            "flight_time_min": round(hours * 60, 2),
            "flight_time_h": round(hours, 3),
        }

    def battery_health(self, *, cycles: int, measured_capacity_mah: float, rated_capacity_mah: float, ir_increase_pct: float = 0.0) -> dict[str, Any]:
        soh = measured_capacity_mah / max(rated_capacity_mah, 1e-9)
        status = "good" if soh >= 0.9 and ir_increase_pct < 30 else "degraded" if soh >= 0.75 else "replace"
        return {
            "cycles": cycles,
            "soh": round(soh, 3),
            "status": status,
            "ir_increase_pct": ir_increase_pct,
            "measured_capacity_mah": measured_capacity_mah,
            "rated_capacity_mah": rated_capacity_mah,
        }

    def get(self, pack_id: str) -> dict[str, Any]:
        item = self.store.battery_packs.get(pack_id)
        if item is None:
            raise NotFoundError("battery_pack", pack_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.battery_packs.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "battery_engineering": "1.0",
            "cell_types": list(CELL_PROFILES.keys()),
            "pack_count": self.store.battery_packs.count(),
            "capabilities": [
                "pack_builder",
                "18650",
                "21700",
                "li_ion",
                "lipo",
                "series_parallel",
                "capacity",
                "voltage",
                "internal_resistance",
                "flight_time",
                "health",
            ],
        }


battery_engineering = BatteryEngineering()
