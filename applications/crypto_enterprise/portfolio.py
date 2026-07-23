"""Portfolio management — wallets, allocation, PnL, balance history."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PortfolioManagement:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def register_portfolio(self, *, name: str, owner: str = "", base_currency: str = "USD") -> dict[str, Any]:
        if not name:
            raise ValidationError("portfolio name required")
        pid = _id("ce_pf")
        return self.store.portfolios.save(
            pid,
            {
                "portfolio_id": pid,
                "name": name,
                "owner": owner,
                "base_currency": base_currency.upper(),
                "created_at": _now(),
            },
        )

    def register_wallet(
        self,
        *,
        portfolio_id: str,
        address: str,
        blockchain_id: str = "",
        label: str = "",
    ) -> dict[str, Any]:
        if self.store.portfolios.get(portfolio_id) is None:
            raise NotFoundError("portfolio", portfolio_id)
        if not address:
            raise ValidationError("wallet address required")
        wid = _id("ce_wal")
        return self.store.wallets.save(
            wid,
            {
                "wallet_id": wid,
                "portfolio_id": portfolio_id,
                "address": address,
                "blockchain_id": blockchain_id,
                "label": label,
                "created_at": _now(),
            },
        )

    def allocate(
        self,
        *,
        portfolio_id: str,
        asset: str,
        weight_pct: float,
        amount: float = 0.0,
    ) -> dict[str, Any]:
        if self.store.portfolios.get(portfolio_id) is None:
            raise NotFoundError("portfolio", portfolio_id)
        weight = float(weight_pct)
        if weight < 0 or weight > 100:
            raise ValidationError("weight_pct must be 0..100")
        aid = _id("ce_alloc")
        return self.store.allocations.save(
            aid,
            {
                "allocation_id": aid,
                "portfolio_id": portfolio_id,
                "asset": asset.upper(),
                "weight_pct": weight,
                "amount": float(amount),
                "at": _now(),
            },
        )

    def track_pnl(
        self,
        *,
        portfolio_id: str,
        realized: float,
        unrealized: float,
    ) -> dict[str, Any]:
        if self.store.portfolios.get(portfolio_id) is None:
            raise NotFoundError("portfolio", portfolio_id)
        pid = _id("ce_pnl")
        realized_f = float(realized)
        unrealized_f = float(unrealized)
        return self.store.pnl.save(
            pid,
            {
                "pnl_id": pid,
                "portfolio_id": portfolio_id,
                "realized": realized_f,
                "unrealized": unrealized_f,
                "total": round(realized_f + unrealized_f, 8),
                "at": _now(),
            },
        )

    def balance_snapshot(
        self,
        *,
        portfolio_id: str,
        balances: dict[str, float] | None = None,
        total_value: float = 0.0,
    ) -> dict[str, Any]:
        if self.store.portfolios.get(portfolio_id) is None:
            raise NotFoundError("portfolio", portfolio_id)
        bid = _id("ce_bal")
        return self.store.balance_history.save(
            bid,
            {
                "balance_id": bid,
                "portfolio_id": portfolio_id,
                "balances": balances or {},
                "total_value": float(total_value),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "portfolios": self.store.portfolios.count(),
            "wallets": self.store.wallets.count(),
            "allocations": self.store.allocations.count(),
            "pnl_entries": self.store.pnl.count(),
            "balance_snapshots": self.store.balance_history.count(),
        }
