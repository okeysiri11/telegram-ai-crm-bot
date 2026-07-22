# Gate Control Engine — check-in/out, appointments, queue, OCR/QR abstractions.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.operations.service import OperationsService, operations_service
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Gate, GateStatus
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminal_operations.events import (
    GateApprovedEvent,
    GateRejectedEvent,
    TruckArrivedEvent,
    TruckDepartedEvent,
)
from applications.port_erp.terminal_operations.models import (
    GateAppointment,
    GateVisit,
    GateVisitStatus,
)


class GateControlEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        operations: OperationsService | None = None,
    ) -> None:
        self._store = store or port_store
        self._operations = operations or operations_service

    def register_gate(self, gate: Gate) -> Gate:
        return self._operations.register_gate(gate)

    def list_gates(self, *, port_id: str | None = None) -> list[Gate]:
        return self._operations.list_gates(port_id=port_id)

    def get_gate(self, gate_id: str) -> Gate:
        return self._operations.get_gate(gate_id)

    def create_appointment(self, appointment: GateAppointment) -> GateAppointment:
        self.get_gate(appointment.gate_id)
        if not appointment.plate_number:
            raise ValidationError("plate_number is required")
        return self._store.gate_appointments.save(appointment.appointment_id, appointment)

    def list_appointments(self, *, gate_id: str | None = None) -> list[GateAppointment]:
        items = self._store.gate_appointments.list_all()
        if gate_id:
            items = [a for a in items if a.gate_id == gate_id]
        return items

    def _next_queue_position(self, gate_id: str) -> int:
        queued = [
            v
            for v in self._store.gate_visits.list_all()
            if v.gate_id == gate_id and v.status in (GateVisitStatus.QUEUED, GateVisitStatus.CHECKED_IN)
        ]
        return len(queued) + 1

    def read_ocr_plate(self, image_ref: str = "", plate_hint: str = "") -> str:
        """OCR abstraction — returns plate hint or derived stub from image_ref."""
        if plate_hint:
            return plate_hint.strip().upper()
        if image_ref:
            return image_ref.split("/")[-1].split(".")[0].upper()[:10] or "UNKNOWN"
        return "UNKNOWN"

    def read_qr_code(self, qr_payload: str = "") -> dict:
        """QR abstraction — parses `key=value&...` or returns raw token."""
        if not qr_payload:
            return {"token": "", "valid": False}
        if "=" in qr_payload:
            parts = dict(p.split("=", 1) for p in qr_payload.split("&") if "=" in p)
            return {"token": qr_payload, "valid": True, **parts}
        return {"token": qr_payload, "valid": True, "driver_id": qr_payload}

    def verify_driver(self, *, driver_id: str, driver_name: str = "", access_list: list[str] | None = None) -> bool:
        if not driver_id and not driver_name:
            return False
        if access_list is not None:
            return driver_id in access_list or driver_name in access_list
        return True

    async def check_in(
        self,
        *,
        gate_id: str,
        plate_number: str = "",
        driver_name: str = "",
        driver_id: str = "",
        appointment_id: str = "",
        container_id: str = "",
        ocr_image_ref: str = "",
        qr_payload: str = "",
        access_list: list[str] | None = None,
    ) -> GateVisit:
        gate = self.get_gate(gate_id)
        if gate.status != GateStatus.OPEN:
            raise ValidationError("gate is not open")

        ocr_plate = self.read_ocr_plate(image_ref=ocr_image_ref, plate_hint=plate_number)
        qr = self.read_qr_code(qr_payload)
        resolved_driver = driver_id or str(qr.get("driver_id", ""))
        plate = plate_number or ocr_plate

        visit = GateVisit(
            gate_id=gate_id,
            terminal_id=gate.terminal_id,
            plate_number=plate,
            driver_name=driver_name,
            driver_id=resolved_driver,
            appointment_id=appointment_id,
            container_id=container_id,
            status=GateVisitStatus.QUEUED,
            ocr_plate=ocr_plate,
            qr_code=str(qr.get("token", "")),
            queue_position=self._next_queue_position(gate_id),
            checked_in_at=time.time(),
        )

        if appointment_id:
            appt = self._store.gate_appointments.get(appointment_id)
            if appt is None:
                raise NotFoundError("GateAppointment", appointment_id)
            appt.status = "arrived"
            self._store.gate_appointments.save(appointment_id, appt)

        if not self.verify_driver(driver_id=resolved_driver, driver_name=driver_name, access_list=access_list):
            visit.status = GateVisitStatus.REJECTED
            visit.access_granted = False
            visit.rejection_reason = "driver_verification_failed"
            saved = self._store.gate_visits.save(visit.visit_id, visit)
            await publish(
                GateRejectedEvent(
                    visit_id=saved.visit_id,
                    gate_id=gate_id,
                    plate_number=plate,
                    reason=saved.rejection_reason,
                )
            )
            return saved

        visit.status = GateVisitStatus.CHECKED_IN
        saved = self._store.gate_visits.save(visit.visit_id, visit)
        await publish(
            TruckArrivedEvent(
                visit_id=saved.visit_id,
                gate_id=gate_id,
                plate_number=plate,
                terminal_id=gate.terminal_id,
            )
        )
        return saved

    async def approve(self, visit_id: str) -> GateVisit:
        visit = self._get_visit(visit_id)
        visit.status = GateVisitStatus.APPROVED
        visit.access_granted = True
        saved = self._store.gate_visits.save(visit_id, visit)
        await publish(
            GateApprovedEvent(
                visit_id=visit_id,
                gate_id=saved.gate_id,
                plate_number=saved.plate_number,
            )
        )
        return saved

    async def reject(self, visit_id: str, *, reason: str = "access_denied") -> GateVisit:
        visit = self._get_visit(visit_id)
        visit.status = GateVisitStatus.REJECTED
        visit.access_granted = False
        visit.rejection_reason = reason
        saved = self._store.gate_visits.save(visit_id, visit)
        await publish(
            GateRejectedEvent(
                visit_id=visit_id,
                gate_id=saved.gate_id,
                plate_number=saved.plate_number,
                reason=reason,
            )
        )
        return saved

    async def check_out(self, visit_id: str) -> GateVisit:
        visit = self._get_visit(visit_id)
        visit.status = GateVisitStatus.CHECKED_OUT
        visit.checked_out_at = time.time()
        saved = self._store.gate_visits.save(visit_id, visit)
        await publish(
            TruckDepartedEvent(
                visit_id=visit_id,
                gate_id=saved.gate_id,
                plate_number=saved.plate_number,
                terminal_id=saved.terminal_id,
            )
        )
        return saved

    def queue(self, gate_id: str) -> list[GateVisit]:
        items = [
            v
            for v in self._store.gate_visits.list_all()
            if v.gate_id == gate_id
            and v.status in (GateVisitStatus.QUEUED, GateVisitStatus.CHECKED_IN, GateVisitStatus.APPROVED)
        ]
        return sorted(items, key=lambda v: v.queue_position or v.created_at)

    def list_visits(self, *, gate_id: str | None = None) -> list[GateVisit]:
        items = self._store.gate_visits.list_all()
        if gate_id:
            items = [v for v in items if v.gate_id == gate_id]
        return items

    def _get_visit(self, visit_id: str) -> GateVisit:
        visit = self._store.gate_visits.get(visit_id)
        if visit is None:
            raise NotFoundError("GateVisit", visit_id)
        return visit


gate_control_engine = GateControlEngine()
