"""Mission operations analytics (Sprint 11.7)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MissionAnalytics:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def _save(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        aid = f"anx_{uuid.uuid4().hex[:12]}"
        item = {"analytics_id": aid, "kind": kind, "created_at": _now(), **payload}
        self.store.ops_analytics.save(aid, item)
        return item

    def flight_statistics(self, *, flights: list[dict[str, Any]]) -> dict[str, Any]:
        hours = [float(f.get("hours", 0)) for f in flights]
        return self._save("flight_statistics", {"flight_count": len(flights), "total_hours": round(sum(hours), 2), "avg_hours": round(mean(hours), 2) if hours else 0})

    def mission_success_rate(self, *, reports: list[dict[str, Any]]) -> dict[str, Any]:
        if not reports:
            return self._save("success_rate", {"rate": 0.0, "total": 0, "successes": 0})
        successes = sum(1 for r in reports if r.get("success"))
        return self._save("success_rate", {"rate": round(successes / len(reports), 3), "total": len(reports), "successes": successes})

    def coverage_analysis(self, *, planned_area_km2: float, covered_area_km2: float) -> dict[str, Any]:
        ratio = covered_area_km2 / max(planned_area_km2, 1e-9)
        return self._save("coverage", {"planned_area_km2": planned_area_km2, "covered_area_km2": covered_area_km2, "coverage_ratio": round(ratio, 3)})

    def battery_consumption(self, *, start_pct: float, end_pct: float, duration_min: float) -> dict[str, Any]:
        drain = start_pct - end_pct
        return self._save("battery", {"start_pct": start_pct, "end_pct": end_pct, "drain_pct": drain, "drain_per_min": round(drain / max(duration_min, 1e-9), 3)})

    def navigation_accuracy(self, *, errors_m: list[float]) -> dict[str, Any]:
        return self._save("nav_accuracy", {"samples": len(errors_m), "avg_error_m": round(mean(errors_m), 3) if errors_m else None, "max_error_m": max(errors_m) if errors_m else None})

    def telemetry_analytics(self, *, samples: list[dict[str, Any]]) -> dict[str, Any]:
        return self._save("telemetry", {"sample_count": len(samples), "keys": sorted({k for s in samples for k in s.keys()})})

    def flight_efficiency(self, *, distance_m: float, energy_wh: float) -> dict[str, Any]:
        m_per_wh = distance_m / max(energy_wh, 1e-9)
        return self._save("efficiency", {"distance_m": distance_m, "energy_wh": energy_wh, "meters_per_wh": round(m_per_wh, 2)})

    def operator_performance(self, *, operator_id: str, missions: int, successes: int) -> dict[str, Any]:
        rate = successes / max(missions, 1)
        return self._save("operator", {"operator_id": operator_id, "missions": missions, "successes": successes, "success_rate": round(rate, 3)})

    def mission_heatmaps(self, *, points: list[dict[str, float]]) -> dict[str, Any]:
        return self._save("heatmap", {"point_count": len(points), "points": points[:500]})

    def historical_comparisons(self, *, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        return self._save("historical", {"left": left, "right": right, "delta_success": float(right.get("success_rate", 0)) - float(left.get("success_rate", 0))})

    def status(self) -> dict[str, Any]:
        return {
            "mission_analytics": "1.0",
            "record_count": self.store.ops_analytics.count(),
            "capabilities": [
                "flight_statistics",
                "mission_success_rate",
                "coverage_analysis",
                "battery_consumption",
                "navigation_accuracy",
                "telemetry_analytics",
                "flight_efficiency",
                "operator_performance",
                "mission_heatmaps",
                "historical_comparisons",
            ],
        }


mission_analytics = MissionAnalytics()
