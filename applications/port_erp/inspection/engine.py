# Inspection Engine — customs / random / risk-based inspections.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.customs.events import CustomsInspectionStartedEvent
from applications.port_erp.customs.models import (
    CustomsChannel,
    InspectionRecord,
    InspectionStatus,
    InspectionType,
)
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class InspectionEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def schedule(self, record: InspectionRecord) -> InspectionRecord:
        if not record.declaration_id and not record.cargo_id:
            raise ValidationError("declaration_id or cargo_id is required")
        return self._store.inspections.save(record.inspection_id, record)

    def get(self, inspection_id: str) -> InspectionRecord:
        item = self._store.inspections.get(inspection_id)
        if item is None:
            raise NotFoundError("InspectionRecord", inspection_id)
        return item

    def list_inspections(self, *, declaration_id: str | None = None) -> list[InspectionRecord]:
        items = self._store.inspections.list_all()
        if declaration_id:
            items = [i for i in items if i.declaration_id == declaration_id]
        return items

    async def start(self, inspection_id: str) -> InspectionRecord:
        item = self.get(inspection_id)
        item.status = InspectionStatus.IN_PROGRESS
        item.started_at = time.time()
        saved = self._store.inspections.save(inspection_id, item)
        await publish(
            CustomsInspectionStartedEvent(
                inspection_id=inspection_id,
                declaration_id=saved.declaration_id,
                cargo_id=saved.cargo_id,
                inspection_type=saved.inspection_type.value,
            )
        )
        return saved

    def complete(self, inspection_id: str, *, passed: bool = True, notes: str = "") -> InspectionRecord:
        item = self.get(inspection_id)
        item.status = InspectionStatus.PASSED if passed else InspectionStatus.FAILED
        item.notes = notes or item.notes
        item.completed_at = time.time()
        return self._store.inspections.save(inspection_id, item)

    def schedule_random(
        self,
        *,
        declaration_id: str,
        cargo_id: str = "",
        channel: CustomsChannel = CustomsChannel.YELLOW,
    ) -> InspectionRecord:
        return self.schedule(
            InspectionRecord(
                declaration_id=declaration_id,
                cargo_id=cargo_id,
                inspection_type=InspectionType.RANDOM,
                channel=channel,
            )
        )


inspection_engine = InspectionEngine()
