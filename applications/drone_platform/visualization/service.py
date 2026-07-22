"""Flight / mission visualization charts (Sprint 11.3)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class VisualizationService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def _save(self, chart_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        cid = f"viz_{uuid.uuid4().hex[:12]}"
        chart = {"chart_id": cid, "chart_type": chart_type, "created_at": _now(), **payload}
        self.store.visualization_charts.save(cid, chart)
        return chart

    def flight_timeline(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        points = [{"t": s.get("recorded_at"), "event": s.get("event", "sample")} for s in samples]
        return self._save("flight_timeline", {"points": points, "count": len(points)})

    def mission_timeline(self, waypoints: list[dict[str, Any]]) -> dict[str, Any]:
        points = [{"seq": wp.get("sequence", i), "lat": wp.get("lat"), "lon": wp.get("lon"), "alt": wp.get("alt")} for i, wp in enumerate(waypoints)]
        return self._save("mission_timeline", {"points": points, "count": len(points)})

    def parameter_changes(self, changes: list[dict[str, Any]]) -> dict[str, Any]:
        return self._save("parameter_changes", {"changes": changes, "count": len(changes)})

    def battery_chart(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        series = [{"t": s.get("recorded_at"), "battery": s.get("battery"), "voltage": s.get("voltage")} for s in samples]
        return self._save("battery_chart", {"series": series})

    def gps_track(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        track = [{"lat": s.get("lat"), "lon": s.get("lon"), "alt": s.get("alt")} for s in samples if s.get("lat") is not None]
        return self._save("gps_track", {"track": track, "point_count": len(track)})

    def altitude_graph(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        series = [{"t": s.get("recorded_at"), "alt": s.get("alt")} for s in samples]
        return self._save("altitude_graph", {"series": series})

    def speed_graph(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        series = [{"t": s.get("recorded_at"), "speed": s.get("speed") or s.get("groundspeed")} for s in samples]
        return self._save("speed_graph", {"series": series})

    def current_consumption(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        series = [{"t": s.get("recorded_at"), "current": s.get("current")} for s in samples]
        return self._save("current_consumption", {"series": series})

    def signal_quality_graph(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        series = [{"t": s.get("recorded_at"), "rssi": s.get("rssi")} for s in samples]
        return self._save("signal_quality_graph", {"series": series})

    def flight_events_timeline(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        return self._save("flight_events_timeline", {"events": events, "count": len(events)})

    def build_bundle(self, samples: list[dict[str, Any]], *, waypoints: list[dict[str, Any]] | None = None, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "flight_timeline": self.flight_timeline(samples),
            "mission_timeline": self.mission_timeline(waypoints or []),
            "battery_chart": self.battery_chart(samples),
            "gps_track": self.gps_track(samples),
            "altitude_graph": self.altitude_graph(samples),
            "speed_graph": self.speed_graph(samples),
            "current_consumption": self.current_consumption(samples),
            "signal_quality_graph": self.signal_quality_graph(samples),
            "flight_events_timeline": self.flight_events_timeline(events or []),
        }

    def list(self) -> list[dict[str, Any]]:
        return self.store.visualization_charts.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "visualization": "1.0",
            "chart_count": self.store.visualization_charts.count(),
            "chart_types": [
                "flight_timeline",
                "mission_timeline",
                "parameter_changes",
                "battery_chart",
                "gps_track",
                "altitude_graph",
                "speed_graph",
                "current_consumption",
                "signal_quality_graph",
                "flight_events_timeline",
            ],
        }


visualization_service = VisualizationService()
