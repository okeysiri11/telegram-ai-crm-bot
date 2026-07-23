"""Finance dashboards and knowledge graph."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FinanceKnowledge:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.bases = list(DEFAULT_CONFIG.knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("fe_kg")
        return self.store.knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"fe:{base}:{key}",
                "at": _now(),
            },
        )

    def relate(self, *, from_node: str, to_node: str, relation: str = "related_to") -> dict[str, Any]:
        if not from_node or not to_node:
            raise ValidationError("from_node and to_node required")
        rid = _id("fe_rel")
        return self.store.knowledge_relationships.save(
            rid,
            {
                "relationship_id": rid,
                "from_node": from_node,
                "to_node": to_node,
                "relation": relation,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entries": self.store.knowledge.count(),
            "relationships": self.store.knowledge_relationships.count(),
            "bases": self.bases,
        }


class FinanceDashboard:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.types = list(DEFAULT_CONFIG.dashboard_types)

    def render(self, *, dashboard_type: str = "overview") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "overview": {
                "organizations": self.store.organizations.count(),
                "journal_entries": self.store.journal_entries.count(),
                "currencies": self.store.currencies.count(),
            },
            "accounts": {
                "coa": self.store.chart_of_accounts.count(),
                "balances": self.store.account_balances.count(),
                "financial_accounts": self.store.financial_accounts.count(),
            },
            "cash": {
                "postings": self.store.ledger_postings.count(),
                "trial_balances": self.store.trial_balances.count(),
            },
            "currency": {
                "rates": self.store.exchange_rates.count(),
                "conversions": self.store.fx_conversions.count(),
                "historical": self.store.historical_rates.count(),
            },
            "health": {
                "events": self.store.events.count(),
                "audit": self.store.audit_trail.count(),
                "knowledge": self.store.knowledge.count(),
            },
        }[dashboard_type]
        did = _id("fe_dash")
        return self.store.dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.dashboards.count(), "types": self.types}
