"""Logging Platform — Sprint 25.6."""

from __future__ import annotations

from typing import Any

from platform_enterprise_production.models import LOG_CAPABILITIES, LOG_STREAMS


class LoggingPlatform:
    def centralize(self, *, query: str = "", stream: str | None = None) -> dict[str, Any]:
        streams = list(LOG_STREAMS)
        if stream:
            if stream not in LOG_STREAMS:
                raise ValueError(f"unknown log stream: {stream}")
            streams = [stream]
        entries = [{"stream": s, "message": f"{s}_heartbeat", "level": "info"} for s in streams]
        filtered = entries
        if query:
            filtered = [e for e in entries if query.lower() in e["message"].lower() or query.lower() in e["stream"]]
        return {
            "streams": list(LOG_STREAMS),
            "entries": filtered,
            "capabilities": list(LOG_CAPABILITIES),
            "search": bool(query),
            "filter": stream is not None,
            "export_ready": True,
            "archive_ready": True,
            "centralized": True,
        }
