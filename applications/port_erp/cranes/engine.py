# Crane Scheduling Engine — STS / RTG / RMG assignments.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.equipment.engine import EquipmentManager, equipment_manager
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminal_operations.events import CraneAssignedEvent, CraneFinishedEvent
from applications.port_erp.terminal_operations.models import (
    CraneAssignment,
    EquipmentStatus,
    EquipmentType,
)


_CRANE_TYPES = {EquipmentType.STS, EquipmentType.RTG, EquipmentType.RMG}


class CraneSchedulingEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        equipment: EquipmentManager | None = None,
    ) -> None:
        self._store = store or port_store
        self._equipment = equipment or equipment_manager

    async def assign(
        self,
        *,
        crane_id: str = "",
        vessel_id: str,
        berth_id: str = "",
        voyage_id: str = "",
        terminal_id: str = "",
        prefer_type: EquipmentType = EquipmentType.STS,
    ) -> CraneAssignment:
        if not vessel_id:
            raise ValidationError("vessel_id is required")
        if crane_id:
            crane = self._equipment.get(crane_id)
        else:
            available = [
                e
                for e in self._equipment.available(terminal_id=terminal_id)
                if e.equipment_type in _CRANE_TYPES
            ]
            preferred = [e for e in available if e.equipment_type == prefer_type]
            pool = preferred or available
            if not pool:
                raise ValidationError("no available cranes")
            crane = pool[0]

        if crane.equipment_type not in _CRANE_TYPES:
            raise ValidationError("equipment is not a crane")
        if crane.status not in (EquipmentStatus.AVAILABLE, EquipmentStatus.ASSIGNED):
            raise ValidationError("crane is not available")

        self._equipment.set_status(crane.equipment_id, EquipmentStatus.ASSIGNED)
        assignment = CraneAssignment(
            crane_id=crane.equipment_id,
            vessel_id=vessel_id,
            berth_id=berth_id,
            voyage_id=voyage_id,
            status="assigned",
            started_at=time.time(),
        )
        saved = self._store.crane_assignments.save(assignment.assignment_id, assignment)
        await publish(
            CraneAssignedEvent(
                assignment_id=saved.assignment_id,
                crane_id=saved.crane_id,
                vessel_id=vessel_id,
                berth_id=berth_id,
            )
        )
        return saved

    async def finish(self, assignment_id: str) -> CraneAssignment:
        assignment = self._store.crane_assignments.get(assignment_id)
        if assignment is None:
            raise NotFoundError("CraneAssignment", assignment_id)
        assignment.status = "finished"
        assignment.finished_at = time.time()
        saved = self._store.crane_assignments.save(assignment_id, assignment)
        self._equipment.set_status(saved.crane_id, EquipmentStatus.AVAILABLE)
        await publish(
            CraneFinishedEvent(
                assignment_id=assignment_id,
                crane_id=saved.crane_id,
                vessel_id=saved.vessel_id,
            )
        )
        return saved

    def list_assignments(self, *, vessel_id: str | None = None) -> list[CraneAssignment]:
        items = self._store.crane_assignments.list_all()
        if vessel_id:
            items = [a for a in items if a.vessel_id == vessel_id]
        return items


crane_scheduling_engine = CraneSchedulingEngine()
