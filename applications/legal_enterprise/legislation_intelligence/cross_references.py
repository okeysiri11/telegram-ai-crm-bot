"""Cross references — relationships, dependencies, conflicts, duplicates."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


RELATION_TYPES = (
    "article_relationship",
    "referenced_law",
    "related_regulation",
    "dependency",
    "conflict",
    "duplicate",
)


class CrossReferences:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def link(
        self,
        *,
        from_id: str,
        to_id: str,
        relation: str,
        detail: str = "",
    ) -> dict[str, Any]:
        if not from_id or not to_id:
            raise ValidationError("from_id and to_id required")
        rel = relation.lower().strip()
        if rel not in RELATION_TYPES:
            raise ValidationError(f"relation must be one of {list(RELATION_TYPES)}")
        rid = _id("li_xref")
        return self.store.li_cross_refs.save(
            rid,
            {
                "xref_id": rid,
                "from_id": from_id,
                "to_id": to_id,
                "relation": rel,
                "detail": detail,
                "at": _now(),
            },
        )

    def article_relationship(self, *, from_id: str, to_id: str, detail: str = "") -> dict[str, Any]:
        return self.link(from_id=from_id, to_id=to_id, relation="article_relationship", detail=detail)

    def referenced_law(self, *, from_id: str, to_id: str, detail: str = "") -> dict[str, Any]:
        return self.link(from_id=from_id, to_id=to_id, relation="referenced_law", detail=detail)

    def related_regulation(self, *, from_id: str, to_id: str, detail: str = "") -> dict[str, Any]:
        return self.link(from_id=from_id, to_id=to_id, relation="related_regulation", detail=detail)

    def dependency(self, *, from_id: str, to_id: str, detail: str = "") -> dict[str, Any]:
        return self.link(from_id=from_id, to_id=to_id, relation="dependency", detail=detail)

    def detect_conflict(
        self,
        *,
        document_a: str,
        document_b: str,
        severity: str = "medium",
        detail: str = "",
    ) -> dict[str, Any]:
        if not document_a or not document_b:
            raise ValidationError("document_a and document_b required")
        cid = _id("li_conf")
        row = {
            "conflict_id": cid,
            "document_a": document_a,
            "document_b": document_b,
            "severity": severity,
            "detail": detail or "potential normative conflict",
            "at": _now(),
        }
        self.store.li_conflicts.save(cid, row)
        self.link(
            from_id=document_a,
            to_id=document_b,
            relation="conflict",
            detail=detail or severity,
        )
        return row

    def detect_duplicate(
        self,
        *,
        document_a: str,
        document_b: str,
        similarity: float = 0.9,
        detail: str = "",
    ) -> dict[str, Any]:
        if not document_a or not document_b:
            raise ValidationError("document_a and document_b required")
        did = _id("li_dup")
        row = {
            "duplicate_id": did,
            "document_a": document_a,
            "document_b": document_b,
            "similarity": max(0.0, min(1.0, float(similarity))),
            "detail": detail or "overlapping regulation text",
            "at": _now(),
        }
        self.store.li_duplicates.save(did, row)
        self.link(
            from_id=document_a,
            to_id=document_b,
            relation="duplicate",
            detail=detail or f"similarity={similarity}",
        )
        return row

    def status(self) -> dict[str, Any]:
        return {
            "cross_refs": self.store.li_cross_refs.count(),
            "conflicts": self.store.li_conflicts.count(),
            "duplicates": self.store.li_duplicates.count(),
        }
