"""Procedural timeline — deadlines, limitation periods, risk alerts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ProceduralTimeline:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.deadline_types = list(DEFAULT_CONFIG.cm_deadline_types)

    def register_deadline(
        self,
        *,
        case_id: str,
        deadline_type: str,
        due_on: str,
        title: str = "",
        risk: str = "normal",
    ) -> dict[str, Any]:
        if self.store.cm_cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        dt = deadline_type.lower().strip()
        if dt not in self.deadline_types:
            raise ValidationError(f"deadline_type must be one of {self.deadline_types}")
        if not due_on:
            raise ValidationError("due_on required")
        did = _id("cm_dl")
        return self.store.cm_deadlines.save(
            did,
            {
                "deadline_id": did,
                "case_id": case_id,
                "deadline_type": dt,
                "title": title or dt.replace("_", " ").title(),
                "due_on": due_on,
                "risk": risk,
                "status": "open",
                "created_at": _now(),
            },
        )

    def calculate_deadline(
        self,
        *,
        case_id: str,
        deadline_type: str,
        from_date: str,
        days: int = 30,
    ) -> dict[str, Any]:
        if not from_date:
            raise ValidationError("from_date required")
        try:
            base = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError("from_date must be ISO datetime") from exc
        due = (base + timedelta(days=int(days))).date().isoformat()
        return self.register_deadline(
            case_id=case_id,
            deadline_type=deadline_type,
            due_on=due,
            title=f"Auto-calculated {deadline_type} (+{days}d)",
            risk="watch" if days <= 14 else "normal",
        )

    def risk_alert(
        self, *, deadline_id: str, severity: str = "high", message: str = ""
    ) -> dict[str, Any]:
        deadline = self.store.cm_deadlines.get(deadline_id)
        if deadline is None:
            raise NotFoundError("deadline", deadline_id)
        deadline["risk"] = severity
        self.store.cm_deadlines.save(deadline_id, deadline)
        aid = _id("cm_alert")
        return self.store.cm_deadline_alerts.save(
            aid,
            {
                "alert_id": aid,
                "deadline_id": deadline_id,
                "case_id": deadline["case_id"],
                "severity": severity,
                "message": message or f"Deadline risk: {deadline['title']}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "deadlines": self.store.cm_deadlines.count(),
            "alerts": self.store.cm_deadline_alerts.count(),
            "types": self.deadline_types,
        }
