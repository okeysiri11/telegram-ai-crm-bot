# Corporate Mobility — company fleets, employee assignments, pool, travel.

from __future__ import annotations

import time

from applications.auto_marketplace.fleet.models import MobilityBooking, TravelRequest
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CorporateMobilityEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def assign_employee(self, *, company_id: str, employee_id: str, fleet_vehicle_id: str, department: str = "") -> dict:
        if not company_id or not employee_id or not fleet_vehicle_id:
            raise ValidationError("company_id, employee_id and fleet_vehicle_id are required")
        assignment = {
            "company_id": company_id,
            "employee_id": employee_id,
            "fleet_vehicle_id": fleet_vehicle_id,
            "department": department,
            "at": time.time(),
        }
        self._store.corporate_assignments.save(f"{company_id}:{employee_id}", assignment)
        return assignment

    def book_pool(self, booking: MobilityBooking) -> MobilityBooking:
        if not booking.company_id or not booking.employee_id:
            raise ValidationError("company_id and employee_id are required")
        if not booking.starts_at:
            booking.starts_at = time.time()
        if not booking.ends_at:
            booking.ends_at = booking.starts_at + 4 * 3600
        booking.status = "booked"
        return self._store.mobility_bookings.save(booking.booking_id, booking)

    def calendar(self, *, company_id: str = "", day_start: float = 0.0, day_end: float = 0.0) -> list[MobilityBooking]:
        items = self._store.mobility_bookings.list_all()
        if company_id:
            items = [b for b in items if b.company_id == company_id]
        if day_start and day_end:
            items = [b for b in items if day_start <= b.starts_at <= day_end]
        return sorted(items, key=lambda b: b.starts_at)

    def create_travel_request(self, request: TravelRequest) -> TravelRequest:
        if not request.employee_id or not request.destination:
            raise ValidationError("employee_id and destination are required")
        request.status = "pending"
        return self._store.travel_requests.save(request.request_id, request)

    def approve_travel(self, request_id: str) -> TravelRequest:
        item = self._store.travel_requests.get(request_id)
        if item is None:
            raise NotFoundError("TravelRequest", request_id)
        item.status = "approved"
        return self._store.travel_requests.save(request_id, item)

    def department_analytics(self, company_id: str) -> dict:
        bookings = [b for b in self._store.mobility_bookings.list_all() if b.company_id == company_id]
        by_dept: dict[str, int] = {}
        for b in bookings:
            by_dept[b.department or "unassigned"] = by_dept.get(b.department or "unassigned", 0) + 1
        return {"company_id": company_id, "bookings": len(bookings), "by_department": by_dept}

    def metrics(self) -> dict:
        return {
            "assignments": self._store.corporate_assignments.count(),
            "bookings": self._store.mobility_bookings.count(),
            "travel_requests": self._store.travel_requests.count(),
        }


corporate_mobility_engine = CorporateMobilityEngine()
