# Port documents service.

from __future__ import annotations

from applications.port_erp.shared.exceptions import ValidationError
from applications.port_erp.shared.models import PortDocument
from applications.port_erp.shared.store import PortStore, port_store


class DocumentsService:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def create(self, document: PortDocument) -> PortDocument:
        if not document.title:
            raise ValidationError("title is required")
        return self._store.documents.save(document.document_id, document)

    def list_documents(self, *, related_id: str | None = None) -> list[PortDocument]:
        items = self._store.documents.list_all()
        if related_id:
            items = [d for d in items if d.related_id == related_id]
        return items


documents_service = DocumentsService()
