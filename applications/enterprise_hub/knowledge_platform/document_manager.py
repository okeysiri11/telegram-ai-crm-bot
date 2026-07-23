"""Document manager — corporate documents and metadata."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.knowledge_platform.models import DOC_STATUSES, DOC_TYPES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DocumentManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def ingest(
        self,
        *,
        title: str,
        content: str = "",
        doc_type: str = "markdown",
        owner: str = "platform",
        tags: list[str] | None = None,
        department: str | None = None,
        classification: str = "internal",
        version: str = "1.0",
        source: str | None = None,
    ) -> dict[str, Any]:
        if not title or not str(title).strip():
            raise ValidationError("title is required")
        dt = doc_type.lower().strip()
        if dt not in DOC_TYPES:
            raise ValidationError(f"doc_type must be one of {list(DOC_TYPES)}")
        did = _id("ekp_doc")
        return self.store.ekp_documents.save(
            did,
            {
                "document_id": did,
                "title": title.strip(),
                "content": content,
                "doc_type": dt,
                "owner": owner,
                "tags": tags or [],
                "department": department,
                "classification": classification,
                "version": version,
                "source": source,
                "status": "active",
                "created_at": _now(),
                "updated_at": _now(),
            },
        )

    def get(self, document_id: str) -> dict[str, Any]:
        item = self.store.ekp_documents.get(document_id)
        if not item:
            raise NotFoundError(f"document not found: {document_id}")
        return item

    def set_status(self, *, document_id: str, status: str) -> dict[str, Any]:
        doc = self.get(document_id)
        st = status.lower().strip()
        if st not in DOC_STATUSES:
            raise ValidationError(f"status must be one of {list(DOC_STATUSES)}")
        doc["status"] = st
        doc["updated_at"] = _now()
        return self.store.ekp_documents.save(document_id, doc)

    def list_active(self) -> list[dict[str, Any]]:
        return [d for d in self.store.ekp_documents.list_all() if d.get("status") == "active"]

    def status(self) -> dict[str, Any]:
        return {"documents": self.store.ekp_documents.count(), "types": list(DOC_TYPES)}
