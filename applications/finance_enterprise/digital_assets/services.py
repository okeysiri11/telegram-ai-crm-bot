"""Digital asset dashboards and knowledge graph."""

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


class DigitalAssetKnowledge:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.bases = list(DEFAULT_CONFIG.da_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("da_kg")
        return self.store.da_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"da:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.da_knowledge.count(), "bases": self.bases}


class DigitalAssetDashboard:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.types = list(DEFAULT_CONFIG.da_dashboard_types)

    def render(self, *, dashboard_type: str = "digital_assets") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "digital_assets": {
                "assets": self.store.da_assets.count(),
                "tokens": self.store.da_tokens.count(),
                "blockchains": self.store.da_blockchains.count(),
            },
            "treasury": {
                "operations": self.store.da_operations.count(),
                "custody": self.store.da_custody.count(),
            },
            "portfolio": {
                "ledger": self.store.da_ledger.count(),
                "valuations": self.store.da_portfolio_vals.count(),
                "unrealized": self.store.da_unrealized.count(),
            },
            "wallets": {
                "wallets": self.store.da_wallets.count(),
                "addresses": self.store.da_addresses.count(),
                "balances": self.store.da_wallet_balances.count(),
            },
            "exchange": {
                "links": self.store.da_exchange_links.count(),
                "trades": self.store.da_trades.count(),
                "reconciliations": self.store.da_exchange_recons.count(),
            },
        }[dashboard_type]
        did = _id("da_dash")
        return self.store.da_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.da_dashboards.count(), "types": self.types}
