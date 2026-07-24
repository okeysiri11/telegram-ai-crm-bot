"""Content Calendar — Sprint 22.5."""

from __future__ import annotations

from typing import Any


class ContentCalendar:
    def plan(self, *, days: int = 7, opportunities: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        slots = []
        for i in range(max(1, days)):
            slots.append(
                {
                    "day_offset": i,
                    "kind": "daily_post" if i % 2 == 0 else "promo",
                    "theme": "seasonal" if i == 3 else "service_spotlight",
                }
            )
        for opp in opportunities or []:
            slots.append(
                {
                    "day_offset": 0,
                    "kind": "opportunity",
                    "theme": opp.get("kind", "open_hours"),
                    "source": opp.get("source", "opportunity_engine"),
                }
            )
        slots.extend(
            [
                {"day_offset": 1, "kind": "birthday", "theme": "client_birthday"},
                {"day_offset": 2, "kind": "holiday", "theme": "seasonal_holiday"},
                {"day_offset": 0, "kind": "open_slot_fill", "theme": "free_windows"},
            ]
        )
        return {
            "entries": slots,
            "count": len(slots),
            "calendar_ref": "enterprise_calendar",
            "auto_published": False,
        }
