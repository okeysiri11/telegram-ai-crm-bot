"""Incident response — Sprint 21.4."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IncidentResponse:
    def __init__(self) -> None:
        self._incidents: list[dict[str, Any]] = []

    def open(self, *, title: str, severity: str = "high", source: str = "monitoring") -> dict[str, Any]:
        if not title:
            raise ValueError("title is required")
        item = {
            "incident_id": f"inc_{uuid.uuid4().hex[:12]}",
            "title": title,
            "severity": severity,
            "source": source,
            "status": "open",
            "opened_at": _now(),
        }
        self._incidents.append(item)
        return item

    def list_open(self) -> list[dict[str, Any]]:
        return [i for i in self._incidents if i["status"] == "open"]
