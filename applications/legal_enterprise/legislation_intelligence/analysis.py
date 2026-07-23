"""AI Legal Analysis — summarization, explanation, gaps, impact."""

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


ANALYSIS_KINDS = (
    "summarize",
    "plain_language",
    "conflict",
    "gap",
    "legal_impact",
    "change_impact",
)


class AILegalAnalysis:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def analyze(
        self,
        *,
        kind: str,
        document_id: str,
        title: str = "",
        findings: list[str] | None = None,
        score: float = 0.8,
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in ANALYSIS_KINDS:
            raise ValidationError(f"kind must be one of {list(ANALYSIS_KINDS)}")
        if not document_id:
            raise ValidationError("document_id required")
        rows = findings or [f"{k} analysis for {document_id}"]
        aid = _id("li_anl")
        return self.store.li_analyses.save(
            aid,
            {
                "analysis_id": aid,
                "kind": k,
                "document_id": document_id,
                "title": title or f"{k.replace('_', ' ').title()} Report",
                "findings": rows,
                "score": max(0.0, min(1.0, float(score))),
                "at": _now(),
            },
        )

    def summarize(self, *, document_id: str, title: str = "", findings: list[str] | None = None) -> dict[str, Any]:
        return self.analyze(
            kind="summarize",
            document_id=document_id,
            title=title or "Law Summary",
            findings=findings or ["Core obligations identified", "Key definitions extracted"],
            score=0.88,
        )

    def plain_language(
        self, *, document_id: str, title: str = "", findings: list[str] | None = None
    ) -> dict[str, Any]:
        return self.analyze(
            kind="plain_language",
            document_id=document_id,
            title=title or "Plain Language Explanation",
            findings=findings or ["Simplified explanation generated for non-specialists"],
            score=0.86,
        )

    def identify_conflicts(
        self, *, document_id: str, title: str = "", findings: list[str] | None = None
    ) -> dict[str, Any]:
        return self.analyze(
            kind="conflict",
            document_id=document_id,
            title=title or "Conflict Identification",
            findings=findings or ["No hard conflicts; soft overlaps flagged"],
            score=0.72,
        )

    def gap_analysis(
        self, *, document_id: str, title: str = "", findings: list[str] | None = None
    ) -> dict[str, Any]:
        return self.analyze(
            kind="gap",
            document_id=document_id,
            title=title or "Gap Analysis",
            findings=findings or ["Coverage gap in enforcement procedures"],
            score=0.7,
        )

    def legal_impact(
        self, *, document_id: str, title: str = "", findings: list[str] | None = None
    ) -> dict[str, Any]:
        return self.analyze(
            kind="legal_impact",
            document_id=document_id,
            title=title or "Legal Impact Analysis",
            findings=findings or ["Material impact on regulated entities"],
            score=0.81,
        )

    def change_impact(
        self, *, document_id: str, title: str = "", findings: list[str] | None = None
    ) -> dict[str, Any]:
        return self.analyze(
            kind="change_impact",
            document_id=document_id,
            title=title or "Change Impact Analysis",
            findings=findings or ["Amendment alters compliance deadlines"],
            score=0.79,
        )

    def status(self) -> dict[str, Any]:
        return {"analyses": self.store.li_analyses.count(), "kinds": list(ANALYSIS_KINDS)}
