"""Enterprise reporting (Sprint 11.10)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


REPORT_TYPES = (
    "executive",
    "engineering",
    "production",
    "mission",
    "maintenance",
    "fleet",
    "performance",
    "ai_decision",
)


class EnterpriseReporting:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def generate(self, *, report_type: str, period: str = "monthly", context: dict[str, Any] | None = None) -> dict[str, Any]:
        if report_type not in REPORT_TYPES:
            report_type = "executive"
        rid = f"rpt_{uuid.uuid4().hex[:12]}"
        report = {
            "report_id": rid,
            "report_type": report_type,
            "period": period,
            "sections": self._sections(report_type),
            "context": dict(context or {}),
            "status": "generated",
            "generated_at": _now(),
        }
        self.store.enterprise_reports.save(rid, report)
        return report

    def _sections(self, report_type: str) -> list[str]:
        mapping = {
            "executive": ["kpi", "risks", "roadmap", "certification"],
            "engineering": ["design", "simulation", "pcb", "cad"],
            "production": ["orders", "assembly", "qa", "yield"],
            "mission": ["success_rate", "coverage", "incidents"],
            "maintenance": ["due", "completed", "predictions"],
            "fleet": ["availability", "utilization", "assignment"],
            "performance": ["efficiency", "latency", "uptime"],
            "ai_decision": ["agents", "recommendations", "overrides"],
        }
        return mapping.get(report_type, ["summary"])

    def list_reports(self, *, report_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.enterprise_reports.list_all()
        if report_type:
            items = [i for i in items if i.get("report_type") == report_type]
        return items

    def status(self) -> dict[str, Any]:
        return {"enterprise_reporting": "1.0", "types": list(REPORT_TYPES), "reports": len(self.list_reports()), "ready": True}


enterprise_reporting = EnterpriseReporting()
