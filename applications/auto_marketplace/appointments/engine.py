# Service Appointments — booking, calendar, allocation, reschedule, notify.

from __future__ import annotations

import time

from applications.auto_marketplace.service_centers.models import AppointmentStatus, ServiceAppointment
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ServiceAppointmentEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def book(self, appointment: ServiceAppointment) -> ServiceAppointment:
        if not appointment.center_id or not appointment.customer_id:
            raise ValidationError("center_id and customer_id are required")
        if not appointment.starts_at:
            appointment.starts_at = time.time() + 3600
        if not appointment.ends_at:
            appointment.ends_at = appointment.starts_at + 3600
        appointment.status = AppointmentStatus.BOOKED
        appointment.notifications.append({"event": "booked", "at": time.time()})
        return self._store.service_appointments.save(appointment.appointment_id, appointment)

    def get(self, appointment_id: str) -> ServiceAppointment:
        item = self._store.service_appointments.get(appointment_id)
        if item is None:
            raise NotFoundError("ServiceAppointment", appointment_id)
        return item

    def calendar(self, *, center_id: str = "", day_start: float = 0.0, day_end: float = 0.0) -> list[ServiceAppointment]:
        items = self._store.service_appointments.list_all()
        if center_id:
            items = [a for a in items if a.center_id == center_id]
        if day_start and day_end:
            items = [a for a in items if day_start <= a.starts_at <= day_end]
        return sorted(items, key=lambda a: a.starts_at)

    def allocate(self, appointment_id: str, *, mechanic_id: str = "", bay_id: str = "") -> ServiceAppointment:
        appt = self.get(appointment_id)
        appt.mechanic_id = mechanic_id or appt.mechanic_id
        appt.bay_id = bay_id or appt.bay_id
        appt.notifications.append({"event": "allocated", "at": time.time()})
        return self._store.service_appointments.save(appointment_id, appt)

    def reschedule(self, appointment_id: str, starts_at: float, ends_at: float | None = None) -> ServiceAppointment:
        appt = self.get(appointment_id)
        appt.starts_at = starts_at
        appt.ends_at = ends_at or (starts_at + 3600)
        appt.status = AppointmentStatus.RESCHEDULED
        appt.notifications.append({"event": "rescheduled", "at": time.time(), "starts_at": starts_at})
        return self._store.service_appointments.save(appointment_id, appt)

    def notify(self, appointment_id: str, message: str) -> ServiceAppointment:
        appt = self.get(appointment_id)
        appt.notifications.append({"event": "notify", "message": message, "at": time.time()})
        return self._store.service_appointments.save(appointment_id, appt)

    def metrics(self) -> dict:
        return {"service_appointments": self._store.service_appointments.count()}


service_appointment_engine = ServiceAppointmentEngine()
