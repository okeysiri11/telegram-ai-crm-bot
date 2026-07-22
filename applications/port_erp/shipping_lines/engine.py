# Shipping Line Engine — schedules and voyage planning.

from __future__ import annotations

from applications.port_erp.companies.service import CompanyRegistry, company_registry
from applications.port_erp.multimodal.models import ScheduleStatus, ShippingSchedule
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import ShippingLine
from applications.port_erp.shared.store import PortStore, port_store


class ShippingLineEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        companies: CompanyRegistry | None = None,
    ) -> None:
        self._store = store or port_store
        self._companies = companies or company_registry

    def register_line(self, line: ShippingLine) -> ShippingLine:
        return self._companies.register_shipping_line(line)

    def list_lines(self) -> list[ShippingLine]:
        return self._store.shipping_lines.list_all()

    def get_line(self, shipping_line_id: str) -> ShippingLine:
        return self._companies.get_shipping_line(shipping_line_id)

    def create_schedule(self, schedule: ShippingSchedule) -> ShippingSchedule:
        self.get_line(schedule.shipping_line_id)
        if not schedule.origin_port or not schedule.destination_port:
            raise ValidationError("origin_port and destination_port are required")
        if schedule.eta and schedule.etd and schedule.eta < schedule.etd:
            raise ValidationError("eta must be after etd")
        return self._store.shipping_schedules.save(schedule.schedule_id, schedule)

    def list_schedules(self, *, shipping_line_id: str | None = None) -> list[ShippingSchedule]:
        items = self._store.shipping_schedules.list_all()
        if shipping_line_id:
            items = [s for s in items if s.shipping_line_id == shipping_line_id]
        return items

    def plan_voyage(self, schedule_id: str, *, voyage_number: str = "", vessel_name: str = "") -> ShippingSchedule:
        schedule = self._store.shipping_schedules.get(schedule_id)
        if schedule is None:
            raise NotFoundError("ShippingSchedule", schedule_id)
        if voyage_number:
            schedule.voyage_number = voyage_number
        if vessel_name:
            schedule.vessel_name = vessel_name
        schedule.status = ScheduleStatus.OPEN
        return self._store.shipping_schedules.save(schedule_id, schedule)


shipping_line_engine = ShippingLineEngine()
