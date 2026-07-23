"""Exchange integration — link, sync, trade/transfer import, fees, reconciliation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ExchangeIntegration:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def link_account(self, *, exchange: str, account_ref: str, label: str = "") -> dict[str, Any]:
        if not exchange or not account_ref:
            raise ValidationError("exchange and account_ref required")
        lid = _id("da_link")
        return self.store.da_exchange_links.save(
            lid,
            {
                "link_id": lid,
                "exchange": exchange.lower(),
                "account_ref": account_ref,
                "label": label or exchange,
                "status": "linked",
                "at": _now(),
            },
        )

    def sync_balances(
        self, *, link_id: str, balances: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        if self.store.da_exchange_links.get(link_id) is None:
            raise NotFoundError("exchange_link", link_id)
        sid = _id("da_sync")
        bals = balances or [{"symbol": "USDT", "balance": 0.0}]
        return self.store.da_exchange_syncs.save(
            sid,
            {
                "sync_id": sid,
                "link_id": link_id,
                "balances": bals,
                "balance_count": len(bals),
                "at": _now(),
            },
        )

    def import_trade(
        self,
        *,
        link_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        fee: float = 0.0,
    ) -> dict[str, Any]:
        if self.store.da_exchange_links.get(link_id) is None:
            raise NotFoundError("exchange_link", link_id)
        tid = _id("da_trd")
        trade = self.store.da_trades.save(
            tid,
            {
                "trade_id": tid,
                "link_id": link_id,
                "symbol": symbol.upper(),
                "side": side.lower(),
                "quantity": float(quantity),
                "price": float(price),
                "fee": float(fee),
                "at": _now(),
            },
        )
        if float(fee) > 0:
            fid = _id("da_fee")
            self.store.da_fees.save(
                fid,
                {
                    "fee_id": fid,
                    "link_id": link_id,
                    "trade_id": tid,
                    "amount": float(fee),
                    "at": _now(),
                },
            )
        return trade

    def import_transfer(
        self, *, link_id: str, asset: str, amount: float, direction: str = "in"
    ) -> dict[str, Any]:
        if self.store.da_exchange_links.get(link_id) is None:
            raise NotFoundError("exchange_link", link_id)
        tid = _id("da_xfr")
        return self.store.da_transfers.save(
            tid,
            {
                "transfer_id": tid,
                "link_id": link_id,
                "asset": asset.upper(),
                "amount": float(amount),
                "direction": direction.lower(),
                "at": _now(),
            },
        )

    def reconcile(self, *, link_id: str, books_total: float, exchange_total: float) -> dict[str, Any]:
        if self.store.da_exchange_links.get(link_id) is None:
            raise NotFoundError("exchange_link", link_id)
        rid = _id("da_xrec")
        return self.store.da_exchange_recons.save(
            rid,
            {
                "reconciliation_id": rid,
                "link_id": link_id,
                "books_total": float(books_total),
                "exchange_total": float(exchange_total),
                "variance": round(float(exchange_total) - float(books_total), 8),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "links": self.store.da_exchange_links.count(),
            "syncs": self.store.da_exchange_syncs.count(),
            "trades": self.store.da_trades.count(),
            "transfers": self.store.da_transfers.count(),
            "fees": self.store.da_fees.count(),
            "reconciliations": self.store.da_exchange_recons.count(),
        }
