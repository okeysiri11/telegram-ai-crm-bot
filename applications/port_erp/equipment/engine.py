# Equipment Manager — STS, RTG, RMG, reach stackers, forklifts, trucks, trailers.

from __future__ import annotations

import time

from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminal_operations.models import (
    Equipment,
    EquipmentStatus,
    EquipmentType,
)


class EquipmentManager:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def register(self, equipment: Equipment) -> Equipment:
        if not equipment.name:
            raise ValidationError("name is required")
        return self._store.equipment.save(equipment.equipment_id, equipment)

    def get(self, equipment_id: str) -> Equipment:
        item = self._store.equipment.get(equipment_id)
        if item is None:
            raise NotFoundError("Equipment", equipment_id)
        return item

    def list_equipment(
        self,
        *,
        terminal_id: str | None = None,
        equipment_type: EquipmentType | None = None,
        status: EquipmentStatus | None = None,
    ) -> list[Equipment]:
        items = self._store.equipment.list_all()
        if terminal_id:
            items = [e for e in items if e.terminal_id == terminal_id]
        if equipment_type:
            items = [e for e in items if e.equipment_type == equipment_type]
        if status:
            items = [e for e in items if e.status == status]
        return items

    def set_status(self, equipment_id: str, status: EquipmentStatus | str) -> Equipment:
        item = self.get(equipment_id)
        item.status = EquipmentStatus(status) if isinstance(status, str) else status
        return self._store.equipment.save(equipment_id, item)

    def schedule_maintenance(self, equipment_id: str, *, at: float | None = None) -> Equipment:
        item = self.get(equipment_id)
        item.next_maintenance_at = at if at is not None else time.time() + 7 * 86400
        item.status = EquipmentStatus.MAINTENANCE
        return self._store.equipment.save(equipment_id, item)

    def available(self, *, terminal_id: str = "", equipment_type: EquipmentType | None = None) -> list[Equipment]:
        return self.list_equipment(
            terminal_id=terminal_id or None,
            equipment_type=equipment_type,
            status=EquipmentStatus.AVAILABLE,
        )


equipment_manager = EquipmentManager()
