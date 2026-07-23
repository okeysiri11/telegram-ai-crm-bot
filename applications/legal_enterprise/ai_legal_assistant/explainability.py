"""AI explainability — traces, evidence, confidence, attribution."""

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


class AIExplainability:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def explain(
        self,
        *,
        subject: str,
        reasoning_steps: list[str] | None = None,
        evidence: list[str] | None = None,
        legal_basis: list[str] | None = None,
        citations: list[str] | None = None,
        confidence: float = 0.82,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        if not subject:
            raise ValidationError("subject required")
        eid = _id("aa_exp")
        conf = max(0.0, min(1.0, float(confidence)))
        steps = reasoning_steps or ["Frame issue", "Apply authorities", "State conclusion"]
        return self.store.aa_explanations.save(
            eid,
            {
                "explanation_id": eid,
                "subject": subject,
                "reasoning_trace": steps,
                "evidence_summary": evidence or ["Contract clause 4", "Hearing transcript excerpt"],
                "legal_basis_summary": legal_basis or ["Civil Code Art. 10"],
                "citation_summary": citations or ["JUD-2026-100"],
                "confidence_score": conf,
                "source_attribution": sources or ["statute_db", "case_law_db"],
                "natural_language": (
                    f"Explanation for '{subject}': the assistant applied {len(steps)} reasoning steps "
                    f"with confidence {conf:.0%}."
                ),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"explanations": self.store.aa_explanations.count()}
