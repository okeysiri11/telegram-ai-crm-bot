"""Clause intelligence — detection, validation, comparison."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ClauseIntelligence:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.kinds = list(DEFAULT_CONFIG.di_clause_kinds)

    def detect(self, *, document_id: str = "", contract_id: str = "", text: str = "") -> dict[str, Any]:
        if not document_id and not contract_id and not text:
            raise ValidationError("document_id, contract_id, or text required")
        source = text
        if contract_id:
            ctr = self.store.di_contracts.get(contract_id)
            if ctr is None:
                raise NotFoundError("contract", contract_id)
            source = ctr.get("body", "")
        if document_id:
            doc = self.store.di_documents.get(document_id)
            if doc is None:
                raise NotFoundError("document", document_id)
            source = doc.get("content", "") or source
        found = []
        lower = source.lower()
        for kind in self.kinds:
            if kind.replace("_", " ") in lower or kind in lower:
                found.append({"kind": kind, "confidence": 0.8})
        if not found and source:
            found.append({"kind": "general", "confidence": 0.5})
        did = _id("di_cdet")
        return self.store.di_clause_detections.save(
            did,
            {
                "detection_id": did,
                "document_id": document_id,
                "contract_id": contract_id,
                "clauses": found,
                "count": len(found),
                "at": _now(),
            },
        )

    def classify_clause(self, *, clause_text: str, kind: str) -> dict[str, Any]:
        if not clause_text:
            raise ValidationError("clause_text required")
        k = kind.lower().strip()
        if k not in self.kinds:
            raise ValidationError(f"kind must be one of {self.kinds}")
        cid = _id("di_ccls")
        return self.store.di_clause_classifications.save(
            cid,
            {
                "classification_id": cid,
                "kind": k,
                "text": clause_text,
                "at": _now(),
            },
        )

    def validate_mandatory(self, *, contract_id: str) -> dict[str, Any]:
        ctr = self.store.di_contracts.get(contract_id)
        if ctr is None:
            raise NotFoundError("contract", contract_id)
        mandatory = [c for c in self.store.di_clause_library.list_all() if c.get("mandatory")]
        present_ids = set(ctr.get("clause_ids") or [])
        missing = [c for c in mandatory if c["clause_id"] not in present_ids]
        vid = _id("di_mval")
        return self.store.di_clause_validations.save(
            vid,
            {
                "validation_id": vid,
                "contract_id": contract_id,
                "mandatory_count": len(mandatory),
                "missing": [{"clause_id": c["clause_id"], "title": c["title"]} for c in missing],
                "passed": len(missing) == 0,
                "at": _now(),
            },
        )

    def detect_missing(self, *, contract_id: str) -> dict[str, Any]:
        return self.validate_mandatory(contract_id=contract_id)

    def detect_duplicates(self, *, contract_id: str) -> dict[str, Any]:
        ctr = self.store.di_contracts.get(contract_id)
        if ctr is None:
            raise NotFoundError("contract", contract_id)
        ids = ctr.get("clause_ids") or []
        seen: set[str] = set()
        dups = []
        for cid in ids:
            if cid in seen:
                dups.append(cid)
            seen.add(cid)
        did = _id("di_cdup")
        return self.store.di_clause_duplicates.save(
            did,
            {
                "duplicate_id": did,
                "contract_id": contract_id,
                "duplicates": dups,
                "count": len(dups),
                "at": _now(),
            },
        )

    def compare_clauses(self, *, clause_a: str, clause_b: str) -> dict[str, Any]:
        if not clause_a or not clause_b:
            raise ValidationError("clause_a and clause_b required")
        a = self.store.di_clause_library.get(clause_a)
        b = self.store.di_clause_library.get(clause_b)
        if a is None:
            raise NotFoundError("clause", clause_a)
        if b is None:
            raise NotFoundError("clause", clause_b)
        similar = a.get("kind") == b.get("kind")
        cid = _id("di_ccmp")
        return self.store.di_clause_comparisons.save(
            cid,
            {
                "comparison_id": cid,
                "clause_a": clause_a,
                "clause_b": clause_b,
                "same_kind": similar,
                "similarity": 0.7 if similar else 0.25,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "detections": self.store.di_clause_detections.count(),
            "classifications": self.store.di_clause_classifications.count(),
            "validations": self.store.di_clause_validations.count(),
            "duplicates": self.store.di_clause_duplicates.count(),
            "comparisons": self.store.di_clause_comparisons.count(),
        }
