"""Document comparison — versions, redlines, similarity, approvals."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DocumentComparison:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def compare_versions(
        self,
        *,
        document_a: str,
        document_b: str,
        changes: list[str] | None = None,
    ) -> dict[str, Any]:
        if self.store.di_documents.get(document_a) is None:
            raise NotFoundError("document", document_a)
        if self.store.di_documents.get(document_b) is None:
            raise NotFoundError("document", document_b)
        cid = _id("di_vcmp")
        delta = changes or ["Title updated", "Clause 4 revised"]
        return self.store.di_comparisons.save(
            cid,
            {
                "comparison_id": cid,
                "document_a": document_a,
                "document_b": document_b,
                "changes": delta,
                "change_count": len(delta),
                "at": _now(),
            },
        )

    def track_change(
        self, *, document_id: str, change: str, author: str = ""
    ) -> dict[str, Any]:
        if self.store.di_documents.get(document_id) is None:
            raise NotFoundError("document", document_id)
        if not change:
            raise ValidationError("change required")
        cid = _id("di_chg")
        return self.store.di_changes.save(
            cid,
            {
                "change_id": cid,
                "document_id": document_id,
                "change": change,
                "author": author or "system",
                "at": _now(),
            },
        )

    def generate_redline(
        self, *, document_a: str, document_b: str, summary: str = ""
    ) -> dict[str, Any]:
        if self.store.di_documents.get(document_a) is None:
            raise NotFoundError("document", document_a)
        if self.store.di_documents.get(document_b) is None:
            raise NotFoundError("document", document_b)
        rid = _id("di_red")
        return self.store.di_redlines.save(
            rid,
            {
                "redline_id": rid,
                "document_a": document_a,
                "document_b": document_b,
                "summary": summary or "Redline generated",
                "uri": f"vault://di/redlines/{rid}",
                "at": _now(),
            },
        )

    def similarity(self, *, document_a: str, document_b: str) -> dict[str, Any]:
        a = self.store.di_documents.get(document_a)
        b = self.store.di_documents.get(document_b)
        if a is None:
            raise NotFoundError("document", document_a)
        if b is None:
            raise NotFoundError("document", document_b)
        score = 0.85 if a.get("format") == b.get("format") else 0.4
        sid = _id("di_sim")
        return self.store.di_similarity.save(
            sid,
            {
                "similarity_id": sid,
                "document_a": document_a,
                "document_b": document_b,
                "score": score,
                "at": _now(),
            },
        )

    def request_approval(
        self, *, document_id: str, requester: str, approver: str = ""
    ) -> dict[str, Any]:
        if self.store.di_documents.get(document_id) is None:
            raise NotFoundError("document", document_id)
        aid = _id("di_apr")
        return self.store.di_approvals.save(
            aid,
            {
                "approval_id": aid,
                "document_id": document_id,
                "requester": requester or "system",
                "approver": approver,
                "status": "pending",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "comparisons": self.store.di_comparisons.count(),
            "changes": self.store.di_changes.count(),
            "redlines": self.store.di_redlines.count(),
            "similarity": self.store.di_similarity.count(),
            "approvals": self.store.di_approvals.count(),
        }
