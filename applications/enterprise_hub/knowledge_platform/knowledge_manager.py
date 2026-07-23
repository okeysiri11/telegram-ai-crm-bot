"""Knowledge manager — governance and knowledge base catalog."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.knowledge_platform.document_manager import DocumentManager
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class KnowledgeManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.documents = DocumentManager(self.store)

    def create_base(
        self,
        *,
        name: str,
        description: str = "",
        owner: str = "platform",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        bid = _id("ekp_kb")
        return self.store.ekp_bases.save(
            bid,
            {
                "base_id": bid,
                "name": name.strip(),
                "description": description,
                "owner": owner,
                "document_ids": [],
                "created_at": _now(),
            },
        )

    def attach_document(self, *, base_id: str, document_id: str) -> dict[str, Any]:
        from applications.enterprise_hub.shared.exceptions import NotFoundError

        base = self.store.ekp_bases.get(base_id)
        if not base:
            raise NotFoundError(f"knowledge base not found: {base_id}")
        self.documents.get(document_id)
        ids = list(base.get("document_ids") or [])
        if document_id not in ids:
            ids.append(document_id)
        base["document_ids"] = ids
        base["updated_at"] = _now()
        return self.store.ekp_bases.save(base_id, base)

    def govern(
        self,
        *,
        document_id: str,
        owner: str | None = None,
        classification: str | None = None,
        expires_at: str | None = None,
        access: list[str] | None = None,
    ) -> dict[str, Any]:
        doc = self.documents.get(document_id)
        gid = _id("ekp_gov")
        record = {
            "governance_id": gid,
            "document_id": document_id,
            "owner": owner or doc.get("owner"),
            "classification": classification or doc.get("classification"),
            "expires_at": expires_at,
            "access": access or ["internal"],
            "version": doc.get("version"),
            "at": _now(),
        }
        if owner:
            doc["owner"] = owner
        if classification:
            doc["classification"] = classification
        doc["updated_at"] = _now()
        self.store.ekp_documents.save(document_id, doc)
        return self.store.ekp_governance.save(gid, record)

    def status(self) -> dict[str, Any]:
        return {
            "bases": self.store.ekp_bases.count(),
            "documents": self.store.ekp_documents.count(),
            "governance": self.store.ekp_governance.count(),
        }
