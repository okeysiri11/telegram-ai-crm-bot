# Customs declarations and clearance workflow.

from __future__ import annotations

import time

from events.publisher import publish

from applications.agro_marketplace.export.ai_integration import ExportAIIntegration, export_ai
from applications.agro_marketplace.export.events import CustomsClearedEvent
from applications.agro_marketplace.export.models import CustomsDeclaration, CustomsStatus
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class CustomsService:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: ExportAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or export_ai

    def create_declaration(self, declaration: CustomsDeclaration) -> CustomsDeclaration:
        if not declaration.shipment_id:
            raise ValidationError("shipment_id is required")
        if not declaration.declaration_number:
            declaration.declaration_number = f"CUS-{declaration.declaration_id[:8].upper()}"
        return self._store.customs_declarations.save(declaration.declaration_id, declaration)

    def get(self, declaration_id: str) -> CustomsDeclaration:
        declaration = self._store.customs_declarations.get(declaration_id)
        if declaration is None:
            raise NotFoundError("CustomsDeclaration", declaration_id)
        return declaration

    def list_declarations(self, *, shipment_id: str | None = None) -> list[CustomsDeclaration]:
        items = self._store.customs_declarations.list_all()
        if shipment_id:
            items = [d for d in items if d.shipment_id == shipment_id]
        return items

    async def submit(self, declaration_id: str) -> CustomsDeclaration:
        declaration = self.get(declaration_id)
        declaration.status = CustomsStatus.SUBMITTED
        declaration.submitted_at = time.time()
        return self._store.customs_declarations.save(declaration_id, declaration)

    async def clear(self, declaration_id: str) -> CustomsDeclaration:
        declaration = self.get(declaration_id)
        declaration.status = CustomsStatus.CLEARED
        declaration.cleared_at = time.time()
        saved = self._store.customs_declarations.save(declaration_id, declaration)
        await publish(
            CustomsClearedEvent(
                shipment_id=saved.shipment_id,
                declaration_id=saved.declaration_id,
                country=saved.country,
            )
        )
        return saved


customs_service = CustomsService()
