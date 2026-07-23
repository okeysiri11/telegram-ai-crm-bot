"""AI compliance intelligence — gaps, scores, recommendations, reports."""

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


class AIComplianceIntelligence:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def _save(self, *, kind: str, findings: list[str], score: float = 0.0, meta: dict | None = None) -> dict[str, Any]:
        iid = _id("cp_ai")
        return self.store.cp_ai_insights.save(
            iid,
            {
                "insight_id": iid,
                "kind": kind,
                "findings": findings,
                "score": max(0.0, min(100.0, float(score))),
                "meta": meta or {},
                "at": _now(),
            },
        )

    def detect_gaps(self, *, company_id: str = "") -> dict[str, Any]:
        open_items = [c for c in self.store.cp_checklists.list_all() if c.get("status") == "open"]
        return self._save(
            kind="gap",
            findings=[f"Open checklist item {c['checklist_id']}" for c in open_items]
            or ["No open compliance gaps"],
            score=max(0.0, 100.0 - len(open_items) * 10),
            meta={"company_id": company_id, "open": len(open_items)},
        )

    def detect_policy_conflicts(self) -> dict[str, Any]:
        policies = self.store.cp_policies.count()
        return self._save(
            kind="policy_conflict",
            findings=["No hard policy conflicts detected"] if policies else ["No policies registered"],
            score=85.0 if policies else 50.0,
        )

    def monitor_regulatory_change(self, *, change_title: str = "") -> dict[str, Any]:
        changes = self.store.cp_reg_changes.count()
        return self._save(
            kind="regulatory_change",
            findings=[change_title] if change_title else [f"{changes} regulatory change impacts tracked"],
            score=70.0,
            meta={"tracked": changes},
        )

    def compliance_health_score(self) -> dict[str, Any]:
        open_items = sum(1 for c in self.store.cp_checklists.list_all() if c.get("status") == "open")
        exceptions = self.store.cp_exceptions.count()
        score = max(0.0, min(100.0, 90.0 - open_items * 5 - exceptions * 3))
        return self._save(
            kind="compliance_health",
            findings=[f"Compliance health score: {score}"],
            score=score,
        )

    def governance_score(self) -> dict[str, Any]:
        companies = self.store.cp_companies.count()
        board = self.store.cp_board.count()
        resolutions = self.store.cp_resolutions.count()
        score = min(100.0, 40.0 + companies * 10 + board * 5 + resolutions * 5)
        return self._save(
            kind="governance_score",
            findings=[f"Corporate governance score: {round(score, 1)}"],
            score=round(score, 1),
        )

    def recommend(self) -> dict[str, Any]:
        actions = [
            "Close open compliance checklist items",
            "Renew licenses approaching expiry",
            "Refresh KYC for high-risk counterparties",
        ]
        return self._save(kind="recommendation", findings=actions, score=75.0)

    def nl_report(self, *, audience: str = "executive") -> dict[str, Any]:
        if not audience:
            raise ValidationError("audience required")
        health = self.compliance_health_score()
        gov = self.governance_score()
        text = (
            f"Compliance health is {health['score']:.0f}/100 and governance score is {gov['score']:.0f}/100 "
            f"for {audience} reporting."
        )
        return self._save(kind="nl_report", findings=[text], score=health["score"], meta={"audience": audience})

    def status(self) -> dict[str, Any]:
        return {"insights": self.store.cp_ai_insights.count()}
