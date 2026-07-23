"""Dashboards and knowledge for Crypto Enterprise."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.config import DEFAULT_CONFIG
from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CryptoDashboard:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(DEFAULT_CONFIG.dashboard_types)

    def render(self, *, dashboard_type: str = "market") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "exchange": {
                "exchanges": self.store.exchanges.count(),
                "connections": self.store.exchange_connections.count(),
            },
            "portfolio": {
                "portfolios": self.store.portfolios.count(),
                "wallets": self.store.wallets.count(),
                "pnl": self.store.pnl.count(),
            },
            "market": {
                "spot": self.store.spot_markets.count(),
                "tickers": self.store.tickers.count(),
                "streams": self.store.streams.count(),
            },
            "asset": {
                "coins": self.store.coins.count(),
                "tokens": self.store.tokens.count(),
                "pairs": self.store.pairs.count(),
            },
        }[dashboard_type]
        did = _id("ce_dash")
        return self.store.dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.dashboards.count(), "types": self.types}


class CryptoKnowledge:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(DEFAULT_CONFIG.knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.types:
            raise ValidationError(f"base must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("ce_kg")
        return self.store.knowledge.save(
            rid,
            {
                "entry_id": rid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"ce:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.knowledge.count(), "bases": self.types}
