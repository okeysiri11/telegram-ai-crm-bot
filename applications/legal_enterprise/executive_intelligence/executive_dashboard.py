"""Executive legal dashboard — overview, portfolio, critical events."""

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


OVERVIEW_SECTIONS = (
    "overview",
    "portfolio",
    "critical_events",
    "hearings",
    "compliance_deadlines",
    "high_risk_cases",
    "pending_contracts",
    "open_tasks",
)


class ExecutiveLegalDashboard:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def snapshot(self, *, section: str = "overview", title: str = "", items: list[str] | None = None) -> dict[str, Any]:
        s = section.lower().strip()
        if s not in OVERVIEW_SECTIONS:
            raise ValidationError(f"section must be one of {list(OVERVIEW_SECTIONS)}")
        defaults = {
            "overview": ["Open matters: 42", "Critical alerts: 3", "Risk score: 58"],
            "portfolio": ["Litigation 18", "Advisory 12", "Compliance 8", "Contracts 4"],
            "critical_events": ["Injunction hearing tomorrow", "Regulator inquiry opened"],
            "hearings": ["CASE-1001 — 2026-07-24", "CASE-1008 — 2026-07-28"],
            "compliance_deadlines": ["License renewal 2026-08-01", "Policy attestation 2026-07-31"],
            "high_risk_cases": ["CASE-1001 (critical)", "CASE-1012 (high)"],
            "pending_contracts": ["MSA-44 awaiting GC", "NDA-90 counterparty review"],
            "open_tasks": ["Prepare hearing brief", "File compliance response"],
        }
        eid = _id("ei_ov")
        return self.store.ei_overview.save(
            eid,
            {
                "snapshot_id": eid,
                "section": s,
                "title": title or s.replace("_", " ").title(),
                "items": items or defaults[s],
                "item_count": len(items or defaults[s]),
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"snapshots": self.store.ei_overview.count(), "sections": list(OVERVIEW_SECTIONS)}
