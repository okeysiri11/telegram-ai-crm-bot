"""Resilience visualization — health, nav, comms, safety, recovery timeline, incidents (Sprint 11.9)."""

from __future__ import annotations

from typing import Any


class ResilienceVisualization:
    def health_dashboard(self, *, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        snap = dict(snapshot or {})
        return {"type": "health_dashboard", "overall": snap.get("overall", "unknown"), "snapshot": snap}

    def navigation_dashboard(self, *, session: dict[str, Any] | None = None) -> dict[str, Any]:
        s = dict(session or {})
        return {"type": "navigation_dashboard", "confidence": s.get("confidence", 0), "health": s.get("health", "unknown"), "session": s}

    def communication_dashboard(self, *, link: dict[str, Any] | None = None) -> dict[str, Any]:
        link = dict(link or {})
        return {"type": "communication_dashboard", "active": link.get("active"), "link": link}

    def safety_dashboard(self, *, check: dict[str, Any] | None = None) -> dict[str, Any]:
        check = dict(check or {})
        return {"type": "safety_dashboard", "safe": check.get("safe", True), "violations": check.get("violations", []), "check": check}

    def recovery_timeline(self, *, report: dict[str, Any] | None = None) -> dict[str, Any]:
        report = dict(report or {})
        return {"type": "recovery_timeline", "timeline": report.get("timeline", []), "recovery_id": report.get("recovery_id")}

    def incident_viewer(self, *, incidents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        incidents = list(incidents or [])
        return {"type": "incident_viewer", "incidents": incidents, "count": len(incidents)}

    def status(self) -> dict[str, Any]:
        return {
            "visualization": "1.0",
            "views": [
                "health_dashboard",
                "navigation_dashboard",
                "communication_dashboard",
                "safety_dashboard",
                "recovery_timeline",
                "incident_viewer",
            ],
            "ready": True,
        }


resilience_visualization = ResilienceVisualization()
