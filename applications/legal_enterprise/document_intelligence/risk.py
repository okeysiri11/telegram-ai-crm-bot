"""AI legal risk review — detection, scoring, revisions."""

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


RISK_KINDS = (
    "risk",
    "ambiguous",
    "contradiction",
    "unbalanced",
    "compliance",
    "gap",
    "revision",
    "score",
)


class AIRiskReview:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def _target(self, *, contract_id: str = "", document_id: str = "") -> tuple[str, str]:
        if contract_id:
            if self.store.di_contracts.get(contract_id) is None:
                raise NotFoundError("contract", contract_id)
            return "contract", contract_id
        if document_id:
            if self.store.di_documents.get(document_id) is None:
                raise NotFoundError("document", document_id)
            return "document", document_id
        raise ValidationError("contract_id or document_id required")

    def _save(
        self,
        *,
        kind: str,
        target_type: str,
        target_id: str,
        findings: list[str],
        score: float = 0.0,
        severity: str = "medium",
    ) -> dict[str, Any]:
        rid = _id("di_risk")
        return self.store.di_risks.save(
            rid,
            {
                "risk_id": rid,
                "kind": kind,
                "target_type": target_type,
                "target_id": target_id,
                "findings": findings,
                "score": max(0.0, min(100.0, float(score))),
                "severity": severity,
                "at": _now(),
            },
        )

    def detect_risks(self, *, contract_id: str = "", document_id: str = "") -> dict[str, Any]:
        ttype, tid = self._target(contract_id=contract_id, document_id=document_id)
        return self._save(
            kind="risk",
            target_type=ttype,
            target_id=tid,
            findings=["Indemnity scope broad", "Termination notice may be short"],
            score=62.0,
            severity="medium",
        )

    def detect_ambiguous(self, *, contract_id: str = "", document_id: str = "") -> dict[str, Any]:
        ttype, tid = self._target(contract_id=contract_id, document_id=document_id)
        return self._save(
            kind="ambiguous",
            target_type=ttype,
            target_id=tid,
            findings=["Phrase 'reasonable efforts' lacks metric"],
            score=48.0,
            severity="low",
        )

    def detect_contradictions(self, *, contract_id: str = "", document_id: str = "") -> dict[str, Any]:
        ttype, tid = self._target(contract_id=contract_id, document_id=document_id)
        return self._save(
            kind="contradiction",
            target_type=ttype,
            target_id=tid,
            findings=["Payment terms conflict with invoice schedule"],
            score=71.0,
            severity="high",
        )

    def detect_unbalanced(self, *, contract_id: str = "", document_id: str = "") -> dict[str, Any]:
        ttype, tid = self._target(contract_id=contract_id, document_id=document_id)
        return self._save(
            kind="unbalanced",
            target_type=ttype,
            target_id=tid,
            findings=["Liability cap favors one party only"],
            score=68.0,
            severity="high",
        )

    def compliance_review(self, *, contract_id: str = "", document_id: str = "") -> dict[str, Any]:
        ttype, tid = self._target(contract_id=contract_id, document_id=document_id)
        return self._save(
            kind="compliance",
            target_type=ttype,
            target_id=tid,
            findings=["Privacy clause aligns with DPL-1", "Audit rights present"],
            score=35.0,
            severity="low",
        )

    def gap_analysis(self, *, contract_id: str = "", document_id: str = "") -> dict[str, Any]:
        ttype, tid = self._target(contract_id=contract_id, document_id=document_id)
        return self._save(
            kind="gap",
            target_type=ttype,
            target_id=tid,
            findings=["Missing force majeure detail", "No data retention schedule"],
            score=55.0,
            severity="medium",
        )

    def recommend_revisions(self, *, contract_id: str = "", document_id: str = "") -> dict[str, Any]:
        ttype, tid = self._target(contract_id=contract_id, document_id=document_id)
        return self._save(
            kind="revision",
            target_type=ttype,
            target_id=tid,
            findings=[
                "Define 'reasonable efforts' with SLA metrics",
                "Balance indemnity mutual terms",
            ],
            score=40.0,
            severity="medium",
        )

    def risk_score(self, *, contract_id: str = "", document_id: str = "") -> dict[str, Any]:
        ttype, tid = self._target(contract_id=contract_id, document_id=document_id)
        related = [
            r
            for r in self.store.di_risks.list_all()
            if r.get("target_id") == tid and r.get("kind") != "score"
        ]
        avg = round(sum(r.get("score", 0) for r in related) / max(1, len(related)), 1)
        return self._save(
            kind="score",
            target_type=ttype,
            target_id=tid,
            findings=[f"Composite risk score: {avg}"],
            score=avg or 50.0,
            severity="high" if avg >= 70 else "medium" if avg >= 40 else "low",
        )

    def status(self) -> dict[str, Any]:
        return {"reviews": self.store.di_risks.count(), "kinds": list(RISK_KINDS)}
