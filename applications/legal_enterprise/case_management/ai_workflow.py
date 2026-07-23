"""AI Legal Workflow — risks, progress, recommendations, health score."""

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


class AILegalWorkflow:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def _require_case(self, case_id: str) -> dict[str, Any]:
        case = self.store.cm_cases.get(case_id)
        if case is None:
            raise NotFoundError("case", case_id)
        return case

    def deadline_risk(self, *, case_id: str) -> dict[str, Any]:
        self._require_case(case_id)
        open_dl = [
            d
            for d in self.store.cm_deadlines.list_all()
            if d["case_id"] == case_id and d.get("status") == "open"
        ]
        high = [d for d in open_dl if d.get("risk") in ("high", "critical", "watch")]
        rid = _id("cm_ai_risk")
        return self.store.cm_ai_insights.save(
            rid,
            {
                "insight_id": rid,
                "case_id": case_id,
                "kind": "deadline_risk",
                "open_deadlines": len(open_dl),
                "elevated": len(high),
                "findings": [d["title"] for d in high] or ["No elevated deadline risk"],
                "at": _now(),
            },
        )

    def missing_documents(self, *, case_id: str) -> dict[str, Any]:
        self._require_case(case_id)
        docs = [d for d in self.store.cm_documents.list_all() if d["case_id"] == case_id]
        types = {d["document_type"] for d in docs}
        missing = [t for t in ("legal", "evidence", "filing") if t not in types]
        rid = _id("cm_ai_miss")
        return self.store.cm_ai_insights.save(
            rid,
            {
                "insight_id": rid,
                "case_id": case_id,
                "kind": "missing_documents",
                "missing": missing,
                "findings": missing or ["Document set complete"],
                "at": _now(),
            },
        )

    def progress_analysis(self, *, case_id: str) -> dict[str, Any]:
        case = self._require_case(case_id)
        events = [t for t in self.store.cm_timelines.list_all() if t["case_id"] == case_id]
        rid = _id("cm_ai_prog")
        return self.store.cm_ai_insights.save(
            rid,
            {
                "insight_id": rid,
                "case_id": case_id,
                "kind": "progress",
                "status": case.get("status"),
                "timeline_events": len(events),
                "findings": [f"Case status: {case.get('status')}", f"Timeline events: {len(events)}"],
                "at": _now(),
            },
        )

    def optimize_workflow(self, *, case_id: str) -> dict[str, Any]:
        self._require_case(case_id)
        tasks = [t for t in self.store.cm_tasks.list_all() if t["case_id"] == case_id and t.get("status") == "open"]
        rid = _id("cm_ai_opt")
        return self.store.cm_ai_insights.save(
            rid,
            {
                "insight_id": rid,
                "case_id": case_id,
                "kind": "workflow_optimization",
                "open_tasks": len(tasks),
                "findings": ["Parallelize discovery tasks"] if tasks else ["Workflow balanced"],
                "at": _now(),
            },
        )

    def recommend_next_actions(self, *, case_id: str) -> dict[str, Any]:
        self._require_case(case_id)
        actions = []
        if not any(d["case_id"] == case_id for d in self.store.cm_hearings.list_all()):
            actions.append("Schedule next hearing")
        if not any(d["case_id"] == case_id and d.get("risk") == "high" for d in self.store.cm_deadlines.list_all()):
            actions.append("Review upcoming deadlines")
        actions.append("Update case summary")
        rid = _id("cm_ai_next")
        return self.store.cm_ai_insights.save(
            rid,
            {
                "insight_id": rid,
                "case_id": case_id,
                "kind": "next_actions",
                "actions": actions,
                "findings": actions,
                "at": _now(),
            },
        )

    def health_score(self, *, case_id: str) -> dict[str, Any]:
        self._require_case(case_id)
        docs = sum(1 for d in self.store.cm_documents.list_all() if d["case_id"] == case_id)
        deadlines = [
            d for d in self.store.cm_deadlines.list_all() if d["case_id"] == case_id and d.get("status") == "open"
        ]
        high = sum(1 for d in deadlines if d.get("risk") in ("high", "critical"))
        score = max(0.0, min(100.0, 70.0 + docs * 5.0 - high * 15.0))
        rid = _id("cm_ai_hlt")
        return self.store.cm_ai_insights.save(
            rid,
            {
                "insight_id": rid,
                "case_id": case_id,
                "kind": "health_score",
                "score": round(score, 1),
                "findings": [f"Case health score: {round(score, 1)}"],
                "at": _now(),
            },
        )

    def natural_language_summary(self, *, case_id: str) -> dict[str, Any]:
        case = self._require_case(case_id)
        if not case_id:
            raise ValidationError("case_id required")
        summary = (
            f"Case {case.get('case_number')} ({case.get('title')}) is {case.get('status')} "
            f"with {case.get('priority')} priority, owned by {case.get('owner') or 'unassigned'}."
        )
        rid = _id("cm_ai_sum")
        return self.store.cm_ai_insights.save(
            rid,
            {
                "insight_id": rid,
                "case_id": case_id,
                "kind": "nl_summary",
                "summary": summary,
                "findings": [summary],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"insights": self.store.cm_ai_insights.count()}
