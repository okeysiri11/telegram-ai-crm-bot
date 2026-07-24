"""Smart Booking Engine — Sprint 22.4."""

from __future__ import annotations

from typing import Any
import time

from platform_beauty_client_journey.models import BOOKING_CHANNELS


class SmartBookingEngine:
    def book(
        self,
        *,
        channel: str,
        customer_id: str,
        service_ids: list[str],
        employee_id: str = "",
        branch_id: str = "",
        start: str = "",
        end: str = "",
        auto_pick: bool = False,
        suggestion: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if channel not in BOOKING_CHANNELS:
            raise ValueError(f"unknown booking channel: {channel}")
        if not customer_id or not service_ids:
            raise ValueError("customer_id and service_ids are required")
        started = time.perf_counter()
        picked = dict(suggestion or {})
        if auto_pick:
            employee_id = employee_id or picked.get("employee_id", "auto:master")
            branch_id = branch_id or picked.get("branch_id", "auto:branch")
            start = start or picked.get("start", "2026-07-26T10:00:00Z")
            end = end or picked.get("end", "2026-07-26T11:00:00Z")
        if not all([employee_id, branch_id, start, end]):
            raise ValueError("employee, branch, start, and end are required (or enable auto_pick)")
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "channel": channel,
            "customer_id": customer_id,
            "service_ids": list(service_ids),
            "employee_id": employee_id,
            "branch_id": branch_id,
            "start": start,
            "end": end,
            "multi_service": len(service_ids) > 1,
            "beauty_os_ref": "beauty_os",
            "calendar_ref": "enterprise_calendar",
            "status": "booked",
            "elapsed_ms": elapsed_ms,
            "under_30s": elapsed_ms < 30000,
            "ai_auto_executed": False,
        }
