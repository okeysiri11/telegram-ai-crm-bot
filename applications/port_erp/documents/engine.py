# Cargo Documentation Engine — B/L, waybills, invoices, declarations.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.customs.events import DocumentSignedEvent
from applications.port_erp.customs.models import DocumentStatus, DocumentType, TradeDocument
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class CargoDocumentationEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def document_types(self) -> list[str]:
        return [t.value for t in DocumentType]

    def create(self, document: TradeDocument) -> TradeDocument:
        if not document.title:
            document.title = document.document_type.value.replace("_", " ").title()
        if document.document_type not in DocumentType:
            raise ValidationError("unsupported document type")
        return self._store.trade_documents.save(document.document_id, document)

    def get(self, document_id: str) -> TradeDocument:
        doc = self._store.trade_documents.get(document_id)
        if doc is None:
            raise NotFoundError("TradeDocument", document_id)
        return doc

    def list_documents(
        self,
        *,
        shipment_id: str | None = None,
        cargo_id: str | None = None,
        document_type: DocumentType | None = None,
    ) -> list[TradeDocument]:
        items = self._store.trade_documents.list_all()
        if shipment_id:
            items = [d for d in items if d.shipment_id == shipment_id]
        if cargo_id:
            items = [d for d in items if d.cargo_id == cargo_id]
        if document_type:
            items = [d for d in items if d.document_type == document_type]
        return items

    def issue(self, document_id: str) -> TradeDocument:
        doc = self.get(document_id)
        doc.status = DocumentStatus.ISSUED
        return self._store.trade_documents.save(document_id, doc)

    async def sign(self, document_id: str, *, signed_by: str) -> TradeDocument:
        if not signed_by:
            raise ValidationError("signed_by is required")
        doc = self.get(document_id)
        doc.status = DocumentStatus.SIGNED
        doc.signed_by = signed_by
        doc.signed_at = time.time()
        saved = self._store.trade_documents.save(document_id, doc)
        await publish(
            DocumentSignedEvent(
                document_id=document_id,
                document_type=saved.document_type.value,
                signed_by=signed_by,
            )
        )
        return saved


cargo_documentation_engine = CargoDocumentationEngine()
