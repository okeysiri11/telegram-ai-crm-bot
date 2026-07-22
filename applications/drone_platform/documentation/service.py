from __future__ import annotations

import uuid
from typing import Any

from applications.drone_platform.models.documentation import DOC_TYPES, DocumentationRecord
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


class DocumentationService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create(
        self,
        *,
        title: str,
        doc_type: str,
        content: str = "",
        project_id: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        document_id: str | None = None,
    ) -> DocumentationRecord:
        if doc_type not in DOC_TYPES:
            raise ValidationError(f"Unsupported documentation type: {doc_type}")
        did = document_id or f"doc_{uuid.uuid4().hex[:12]}"
        record = DocumentationRecord(
            document_id=did,
            title=title,
            doc_type=doc_type,
            content=content,
            project_id=project_id,
            tags=list(tags or []),
            metadata=dict(metadata or {}),
        )
        self.store.documents.save(did, record)
        return record

    def get(self, document_id: str) -> DocumentationRecord:
        item = self.store.documents.get(document_id)
        if item is None:
            raise NotFoundError("document", document_id)
        return item

    def list(self, doc_type: str | None = None, project_id: str | None = None) -> list[DocumentationRecord]:
        items = self.store.documents.list_all()
        if doc_type:
            items = [d for d in items if d.doc_type == doc_type]
        if project_id:
            items = [d for d in items if d.project_id == project_id]
        return items

    def supported_types(self) -> list[str]:
        return list(DOC_TYPES)


documentation_service = DocumentationService()
