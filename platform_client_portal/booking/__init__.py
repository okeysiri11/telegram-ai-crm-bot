"""Online Booking — Sprint 22.8."""

from __future__ import annotations

from typing import Any
import time


class OnlineBooking:
    def book(
        self,
        *,
        customer_id: str,
        branch_id: str,
        service_ids: list[str],
        employee_id: str = "",
        start: str = "",
        end: str = "",
        waitlist: bool = False,
        smart_booking_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not customer_id or not branch_id or not service_ids:
            raise ValueError("customer_id, branch_id and service_ids are required")
        started = time.perf_counter()
        if smart_booking_result:
            employee_id = employee_id or smart_booking_result.get("employee_id", "")
            start = start or smart_booking_result.get("start", "")
            end = end or smart_booking_result.get("end", "")
            if smart_booking_result.get("appointment_id"):
                booking_id = smart_booking_result["appointment_id"]
            else:
                booking_id = smart_booking_result.get("booking_id")
        else:
            booking_id = None
        if waitlist and not start:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            return {
                "customer_id": customer_id,
                "branch_id": branch_id,
                "service_ids": list(service_ids),
                "status": "waitlist",
                "smart_booking_ref": "beauty_client_journey",
                "elapsed_ms": elapsed_ms,
                "under_60s": elapsed_ms < 60000,
                "self_service": True,
            }
        if not all([employee_id, start, end]):
            raise ValueError("employee_id, start and end required unless waitlist")
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "customer_id": customer_id,
            "branch_id": branch_id,
            "service_ids": list(service_ids),
            "employee_id": employee_id,
            "start": start,
            "end": end,
            "multi_service": len(service_ids) > 1,
            "status": "booked",
            "booking_id": booking_id,
            "smart_booking_ref": "beauty_client_journey",
            "elapsed_ms": elapsed_ms,
            "under_60s": elapsed_ms < 60000,
            "self_service": True,
        }
