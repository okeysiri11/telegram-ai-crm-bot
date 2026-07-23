"""Document intelligence integration for AI Legal Assistant."""

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


DOC_ACTIONS = (
    "contract_analysis",
    "evidence_review",
    "interpretation",
    "compliance_verification",
    "risk_correlation",
    "cross_document",
)


class DocumentBridge:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def analyze_document(
        self,
        *,
        action: str,
        document_ref: str,
        detail: str = "",
    ) -> dict[str, Any]:
        a = action.lower().strip()
        if a not in DOC_ACTIONS:
            raise ValidationError(f"action must be one of {list(DOC_ACTIONS)}")
        if not document_ref:
            raise ValidationError("document_ref required")
        did = _id("aa_doc")
        return self.store.aa_doc_analyses.save(
            did,
            {
                "analysis_id": did,
                "action": a,
                "document_ref": document_ref,
                "detail": detail or f"{a.replace('_', ' ')} completed",
                "findings": [f"{a} result for {document_ref}"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"document_analyses": self.store.aa_doc_analyses.count(), "actions": list(DOC_ACTIONS)}
