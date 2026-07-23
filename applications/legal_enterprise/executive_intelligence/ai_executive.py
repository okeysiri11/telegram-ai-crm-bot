"""AI executive intelligence — briefings, reports, Q&A."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIExecutiveIntelligence:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.report_types = list(DEFAULT_CONFIG.ei_report_types)

    def report(self, *, report_type: str, audience: str = "executive", focus: str = "") -> dict[str, Any]:
        rt = report_type.lower().strip()
        if rt not in self.report_types:
            raise ValidationError(f"report_type must be one of {self.report_types}")
        templates = {
            "daily_briefing": "Daily executive legal briefing covering critical events and deadlines.",
            "weekly_summary": "Weekly legal summary of matters, hearings, and compliance status.",
            "monthly_risk": "Monthly enterprise legal risk report with trend analysis.",
            "nl_report": "Natural language executive report synthesizing portfolio and risk posture.",
            "strategic_insight": "Strategic legal insight for board-level decision making.",
        }
        rid = _id("ei_rpt")
        narrative = templates[rt]
        if focus:
            narrative = f"{narrative} Focus: {focus}."
        return self.store.ei_reports.save(
            rid,
            {
                "report_id": rid,
                "report_type": rt,
                "audience": audience,
                "focus": focus,
                "narrative": narrative,
                "at": _now(),
            },
        )

    def ask(self, *, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        if not question:
            raise ValidationError("question required")
        qid = _id("ei_qa")
        answer = (
            f"Executive answer: regarding '{question[:120]}', prioritize high-risk matters, "
            "track regulatory exposure, and allocate counsel resources to critical deadlines."
        )
        return self.store.ei_qa.save(
            qid,
            {
                "qa_id": qid,
                "question": question,
                "answer": answer,
                "context": context or {},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "reports": self.store.ei_reports.count(),
            "qa": self.store.ei_qa.count(),
            "report_types": self.report_types,
        }
