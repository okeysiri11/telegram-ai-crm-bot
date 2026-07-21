# DocumentService — marketplace documents registry.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from applications.agro_marketplace.shared.store import AgroStore, agro_store


@dataclass
class AgroDocument:
    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    document_type: str = "contract"
    owner_id: str = ""
    related_id: str = ""
    uri: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "document_type": self.document_type,
            "owner_id": self.owner_id,
            "related_id": self.related_id,
            "uri": self.uri,
            "created_at": self.created_at,
        }


class DocumentService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def create_document(self, document: AgroDocument) -> AgroDocument:
        return self._store.documents.save(document.document_id, document)

    def list_documents(self, *, owner_id: str | None = None) -> list[AgroDocument]:
        items = self._store.documents.list_all()
        if owner_id:
            items = [d for d in items if d.owner_id == owner_id]
        return items


document_service = DocumentService()
