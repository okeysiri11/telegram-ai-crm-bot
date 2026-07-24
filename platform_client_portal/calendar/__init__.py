"""Personal Calendar — Sprint 22.8."""

from __future__ import annotations

from typing import Any


class PersonalCalendar:
    def render(
        self,
        *,
        appointments: list[dict[str, Any]],
        ai_recommendations: list[str] | None = None,
    ) -> dict[str, Any]:
        upcoming = [a for a in appointments if a.get("status") in ("booked", "confirmed", "waiting", "rescheduled")]
        past = [a for a in appointments if a.get("status") in ("completed",)]
        cancelled = [a for a in appointments if a.get("status") == "cancelled"]
        return {
            "upcoming": upcoming,
            "past": past,
            "cancelled": cancelled,
            "ai_recommendations": list(ai_recommendations or []),
            "beauty_os_ref": "beauty_os",
        }
