"""Judicial analytics — timelines and statistical distributions."""

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


ANALYTIC_KINDS = (
    "timeline",
    "regional",
    "court",
    "judge",
    "category",
    "outcome",
)


class JudicialAnalytics:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def report(self, *, kind: str, scope: str = "all") -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in ANALYTIC_KINDS:
            raise ValidationError(f"kind must be one of {list(ANALYTIC_KINDS)}")
        decisions = self.store.ji_decisions.list_all()
        metrics: dict[str, Any]
        if k == "timeline":
            metrics = {
                "points": [
                    {"decision_id": d["decision_id"], "decided_on": d.get("decided_on"), "outcome": d.get("outcome")}
                    for d in decisions
                ],
                "count": len(decisions),
            }
        elif k == "regional":
            regions: dict[str, int] = {}
            for d in decisions:
                region = (d.get("metadata") or {}).get("region") or d.get("court_name") or "unknown"
                regions[str(region)] = regions.get(str(region), 0) + 1
            metrics = {"regions": regions}
        elif k == "court":
            courts: dict[str, int] = {}
            for d in decisions:
                name = d.get("court_name") or "unknown"
                courts[name] = courts.get(name, 0) + 1
            metrics = {"courts": courts}
        elif k == "judge":
            judges: dict[str, int] = {}
            for d in decisions:
                name = d.get("judge_name") or "unknown"
                judges[name] = judges.get(name, 0) + 1
            metrics = {"judges": judges}
        elif k == "category":
            cats: dict[str, int] = {}
            for c in self.store.ji_classifications.list_all():
                if c.get("kind") == "case":
                    label = c.get("label") or "unknown"
                    cats[label] = cats.get(label, 0) + 1
            metrics = {"categories": cats}
        else:
            outcomes: dict[str, int] = {}
            for d in decisions:
                outcome = d.get("outcome") or "unknown"
                outcomes[outcome] = outcomes.get(outcome, 0) + 1
            metrics = {"outcomes": outcomes}
        rid = _id("ji_anlt")
        return self.store.ji_analytics.save(
            rid,
            {
                "report_id": rid,
                "kind": k,
                "scope": scope,
                "metrics": metrics,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"reports": self.store.ji_analytics.count(), "kinds": list(ANALYTIC_KINDS)}
