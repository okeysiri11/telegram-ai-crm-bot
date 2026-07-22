"""Global Command Center — ops center, dashboards, maps, tracking, incidents (Sprint 11.8)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GlobalCommandCenter:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def operations_center(self) -> dict[str, Any]:
        return {
            "center": "global_command",
            "status": "operational",
            "panels": ["fleet_map", "mission_map", "live_tracking", "operators", "incidents", "timeline"],
            "at": _now(),
        }

    def global_dashboard(self) -> dict[str, Any]:
        return {
            "aircraft_online": len(self.store.cloud_tracks.list_all()),
            "active_missions": len([m for m in self.store.ops_missions.list_all() if m.get("status") in {"scheduled", "active", "simulated"}]),
            "open_incidents": len([i for i in self.store.cloud_incidents.list_all() if i.get("status") == "open"]),
            "operators_online": len([s for s in self.store.remote_sessions.list_all() if s.get("status") == "active"]),
            "cloud_nodes": len(self.store.cloud_nodes.list_all()),
            "at": _now(),
        }

    def fleet_map(self, fleets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        fleets = fleets or self.store.cloud_fleets.list_all()
        markers = [
            {
                "id": f.get("cloud_fleet_id"),
                "name": f.get("name"),
                "country": f.get("country"),
                "availability": f.get("availability"),
            }
            for f in fleets
        ]
        return {"type": "fleet_map", "markers": markers, "count": len(markers)}

    def mission_map(self, missions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        missions = missions or self.store.ops_missions.list_all()
        return {
            "type": "mission_map",
            "missions": [{"id": m.get("ops_mission_id"), "name": m.get("name"), "status": m.get("status")} for m in missions],
            "count": len(missions),
        }

    def live_track(self, *, aircraft_id: str, lat: float, lon: float, alt: float = 0, heading: float = 0) -> dict[str, Any]:
        tid = aircraft_id or f"trk_{uuid.uuid4().hex[:10]}"
        track = {
            "track_id": tid,
            "aircraft_id": aircraft_id,
            "lat": lat,
            "lon": lon,
            "alt": alt,
            "heading": heading,
            "updated_at": _now(),
        }
        self.store.cloud_tracks.save(tid, track)
        return track

    def live_aircraft_tracking(self) -> dict[str, Any]:
        tracks = self.store.cloud_tracks.list_all()
        return {"type": "live_tracking", "aircraft": tracks, "count": len(tracks)}

    def operator_dashboard(self, *, operator_id: str = "") -> dict[str, Any]:
        sessions = self.store.remote_sessions.list_all()
        if operator_id:
            sessions = [s for s in sessions if s.get("operator_id") == operator_id]
        return {"type": "operator_dashboard", "sessions": sessions, "count": len(sessions)}

    def raise_incident(
        self,
        *,
        title: str,
        severity: str = "medium",
        aircraft_id: str = "",
        mission_id: str = "",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        iid = f"inc_{uuid.uuid4().hex[:12]}"
        incident = {
            "incident_id": iid,
            "title": title,
            "severity": severity,
            "aircraft_id": aircraft_id,
            "mission_id": mission_id,
            "status": "open",
            "details": dict(details or {}),
            "created_at": _now(),
        }
        self.store.cloud_incidents.save(iid, incident)
        return incident

    def incident_dashboard(self) -> dict[str, Any]:
        incidents = self.store.cloud_incidents.list_all()
        return {
            "type": "incident_dashboard",
            "open": [i for i in incidents if i.get("status") == "open"],
            "all": incidents,
            "count": len(incidents),
        }

    def mission_timeline(self, *, mission_id: str = "", events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        timeline_events = list(events or [])
        if not timeline_events and mission_id:
            mission = self.store.ops_missions.get(mission_id)
            if mission:
                timeline_events = [
                    {"event": "created", "at": mission.get("created_at")},
                    {"event": "status", "value": mission.get("status")},
                ]
        return {"type": "mission_timeline", "mission_id": mission_id, "events": timeline_events}

    def status(self) -> dict[str, Any]:
        return {
            "global_command": "1.0",
            "tracks": len(self.store.cloud_tracks.list_all()),
            "incidents": len(self.store.cloud_incidents.list_all()),
            "ready": True,
        }


global_command = GlobalCommandCenter()
