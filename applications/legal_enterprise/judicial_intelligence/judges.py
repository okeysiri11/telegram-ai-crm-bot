"""Judge intelligence — registry, history, statistics, subject matter, workload."""

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


class JudgeIntelligence:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def register_judge(
        self,
        *,
        full_name: str,
        court_id: str = "",
        court_name: str = "",
        title: str = "Judge",
        subjects: list[str] | None = None,
    ) -> dict[str, Any]:
        if not full_name:
            raise ValidationError("full_name required")
        jid = _id("ji_jdg")
        return self.store.ji_judges.save(
            jid,
            {
                "judge_id": jid,
                "full_name": full_name,
                "court_id": court_id,
                "court_name": court_name,
                "title": title,
                "subjects": subjects or [],
                "created_at": _now(),
            },
        )

    def record_decision(self, *, judge_id: str, decision_id: str) -> dict[str, Any]:
        if self.store.ji_judges.get(judge_id) is None:
            raise NotFoundError("judge", judge_id)
        if self.store.ji_decisions.get(decision_id) is None:
            raise NotFoundError("decision", decision_id)
        hid = _id("ji_jhist")
        return self.store.ji_judge_history.save(
            hid,
            {
                "history_id": hid,
                "judge_id": judge_id,
                "decision_id": decision_id,
                "at": _now(),
            },
        )

    def decision_statistics(self, *, judge_id: str) -> dict[str, Any]:
        if self.store.ji_judges.get(judge_id) is None:
            raise NotFoundError("judge", judge_id)
        linked = [h for h in self.store.ji_judge_history.list_all() if h["judge_id"] == judge_id]
        outcomes: dict[str, int] = {}
        for h in linked:
            dec = self.store.ji_decisions.get(h["decision_id"]) or {}
            outcome = dec.get("outcome") or "unknown"
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
        sid = _id("ji_jstat")
        return self.store.ji_judge_stats.save(
            sid,
            {
                "stat_id": sid,
                "judge_id": judge_id,
                "decision_count": len(linked),
                "outcomes": outcomes,
                "at": _now(),
            },
        )

    def subject_matter_analysis(self, *, judge_id: str) -> dict[str, Any]:
        judge = self.store.ji_judges.get(judge_id)
        if judge is None:
            raise NotFoundError("judge", judge_id)
        subjects = list(judge.get("subjects") or [])
        linked = [h for h in self.store.ji_judge_history.list_all() if h["judge_id"] == judge_id]
        for h in linked:
            for c in self.store.ji_classifications.list_all():
                if c.get("decision_id") == h["decision_id"] and c.get("kind") == "topic":
                    label = c.get("label")
                    if label and label not in subjects:
                        subjects.append(label)
        aid = _id("ji_subj")
        return self.store.ji_subject_analysis.save(
            aid,
            {
                "analysis_id": aid,
                "judge_id": judge_id,
                "subjects": subjects,
                "subject_count": len(subjects),
                "at": _now(),
            },
        )

    def workload_analytics(self, *, judge_id: str, period: str = "ytd") -> dict[str, Any]:
        if self.store.ji_judges.get(judge_id) is None:
            raise NotFoundError("judge", judge_id)
        count = sum(1 for h in self.store.ji_judge_history.list_all() if h["judge_id"] == judge_id)
        wid = _id("ji_work")
        return self.store.ji_workload.save(
            wid,
            {
                "workload_id": wid,
                "judge_id": judge_id,
                "period": period,
                "decision_count": count,
                "load_index": round(min(1.0, count / 20.0), 3),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "judges": self.store.ji_judges.count(),
            "history": self.store.ji_judge_history.count(),
            "stats": self.store.ji_judge_stats.count(),
            "subjects": self.store.ji_subject_analysis.count(),
            "workload": self.store.ji_workload.count(),
        }
