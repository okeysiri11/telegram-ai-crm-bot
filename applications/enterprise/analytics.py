"""Enterprise Analytics — reports and BI (Sprint 12.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise.config import DEFAULT_CONFIG
from applications.enterprise.shared.exceptions import ValidationError
from applications.enterprise.shared.store import EnterpriseStore, enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseAnalytics:
    def __init__(self, store: EnterpriseStore | None = None) -> None:
        self.store = store or enterprise_store
        self.report_types = list(DEFAULT_CONFIG.report_types)

    def generate_report(
        self,
        *,
        report_type: str,
        title: str = "",
        metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if report_type not in self.report_types:
            raise ValidationError(f"report_type must be one of {self.report_types}")
        rid = _id("rpt")
        report = {
            "report_id": rid,
            "report_type": report_type,
            "title": title or f"{report_type} report",
            "metrics": metrics or {"score": 1.0},
            "status": "ready",
            "generated_at": _now(),
        }
        return self.store.reports.save(rid, report)

    def list_reports(self, report_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.reports.list_all()
        if report_type:
            return [r for r in items if r.get("report_type") == report_type]
        return items

    def status(self) -> dict[str, Any]:
        return {
            "reports": len(self.store.reports.list_all()),
            "report_types": self.report_types,
        }


enterprise_analytics = EnterpriseAnalytics()
