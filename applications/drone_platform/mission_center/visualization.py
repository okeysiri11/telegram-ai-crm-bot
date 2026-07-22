"""Mission operations visualization (Sprint 11.7)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.visualization.service import VisualizationService, visualization_service


class MissionOpsVisualization:
    def __init__(self, viz: VisualizationService | None = None) -> None:
        self.viz = viz or visualization_service

    def interactive_map(self, *, tracks: list[dict[str, Any]], waypoints: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {"type": "interactive_map", "tracks": tracks, "waypoints": waypoints or [], "interactive": True}

    def mission_3d_view(self, *, waypoints: list[dict[str, Any]], altitude_scale: float = 1.0) -> dict[str, Any]:
        return {"type": "3d_mission_view", "waypoints": waypoints, "altitude_scale": altitude_scale}

    def aircraft_tracks(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        return self.viz.gps_track(samples)

    def swarm_visualization(self, *, swarm: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "swarm_visualization",
            "swarm_id": swarm.get("swarm_id"),
            "formation": swarm.get("formation"),
            "roles": swarm.get("roles"),
            "fleet_ids": swarm.get("fleet_ids"),
        }

    def coverage_map(self, *, strips: list[dict[str, Any]]) -> dict[str, Any]:
        return {"type": "coverage_map", "strips": strips, "strip_count": len(strips)}

    def flight_timeline(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        return self.viz.flight_timeline(samples)

    def telemetry_charts(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        return self.viz.build_bundle(samples)

    def status(self) -> dict[str, Any]:
        return {
            "mission_ops_visualization": "1.0",
            "capabilities": [
                "interactive_maps",
                "3d_mission_view",
                "aircraft_tracks",
                "swarm_visualization",
                "mission_replay",
                "coverage_maps",
                "flight_timelines",
                "telemetry_charts",
            ],
        }


mission_ops_visualization = MissionOpsVisualization()
