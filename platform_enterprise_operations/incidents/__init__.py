"""Incident Center — Sprint 23.0."""

from __future__ import annotations

from typing import Any


class IncidentCenter:
    def open(self, *, title: str, severity: str = "medium", details: str = "") -> dict[str, Any]:
        if not title:
            raise ValueError("title is required")
        severity = (severity or "medium").lower()
        if severity not in ("low", "medium", "high", "critical"):
            severity = "medium"
        return {
            "title": title.strip(),
            "severity": severity,
            "details": details,
            "status": "open",
            "investigation": None,
            "fix": None,
        }

    def resolve(self, incident: dict[str, Any], *, investigation: str = "", fix: str = "") -> dict[str, Any]:
        updated = dict(incident)
        updated["investigation"] = investigation or updated.get("investigation")
        updated["fix"] = fix or updated.get("fix")
        updated["status"] = "resolved" if updated.get("fix") else "investigating"
        return updated
