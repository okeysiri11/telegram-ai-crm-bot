"""Digital asset accounting — ledger, cost basis, gains/losses, valuation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.shared.exceptions import ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DigitalAssetAccounting:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def post_ledger(
        self,
        *,
        asset_symbol: str,
        quantity: float,
        unit_cost: float,
        side: str = "buy",
        wallet_id: str = "",
    ) -> dict[str, Any]:
        if not asset_symbol:
            raise ValidationError("asset_symbol required")
        qty = float(quantity)
        cost = float(unit_cost)
        if qty <= 0 or cost < 0:
            raise ValidationError("quantity must be positive and unit_cost non-negative")
        side_l = side.lower().strip()
        if side_l not in ("buy", "sell"):
            raise ValidationError("side must be buy or sell")
        lid = _id("da_led")
        return self.store.da_ledger.save(
            lid,
            {
                "ledger_id": lid,
                "asset_symbol": asset_symbol.upper(),
                "quantity": qty,
                "unit_cost": cost,
                "total_cost": round(qty * cost, 8),
                "side": side_l,
                "wallet_id": wallet_id,
                "at": _now(),
            },
        )

    def cost_basis(self, *, asset_symbol: str) -> dict[str, Any]:
        if not asset_symbol:
            raise ValidationError("asset_symbol required")
        sym = asset_symbol.upper()
        buys = [
            e
            for e in self.store.da_ledger.list_all()
            if e["asset_symbol"] == sym and e["side"] == "buy"
        ]
        qty = sum(float(e["quantity"]) for e in buys)
        total = sum(float(e["total_cost"]) for e in buys)
        avg = round(total / qty, 8) if qty else 0.0
        cid = _id("da_cb")
        return self.store.da_cost_basis.save(
            cid,
            {
                "cost_basis_id": cid,
                "asset_symbol": sym,
                "quantity": qty,
                "total_cost": total,
                "average_cost": avg,
                "at": _now(),
            },
        )

    def realized_pnl(
        self, *, asset_symbol: str, sell_quantity: float, sell_price: float, average_cost: float
    ) -> dict[str, Any]:
        qty = float(sell_quantity)
        price = float(sell_price)
        avg = float(average_cost)
        if qty <= 0:
            raise ValidationError("sell_quantity must be positive")
        proceeds = round(qty * price, 8)
        cost = round(qty * avg, 8)
        pnl = round(proceeds - cost, 8)
        rid = _id("da_rpnl")
        return self.store.da_realized.save(
            rid,
            {
                "realized_id": rid,
                "asset_symbol": asset_symbol.upper(),
                "quantity": qty,
                "sell_price": price,
                "average_cost": avg,
                "proceeds": proceeds,
                "cost": cost,
                "realized_pnl": pnl,
                "at": _now(),
            },
        )

    def unrealized_pnl(
        self, *, asset_symbol: str, quantity: float, market_price: float, average_cost: float
    ) -> dict[str, Any]:
        qty = float(quantity)
        mkt = float(market_price)
        avg = float(average_cost)
        mv = round(qty * mkt, 8)
        cb = round(qty * avg, 8)
        uid = _id("da_upnl")
        return self.store.da_unrealized.save(
            uid,
            {
                "unrealized_id": uid,
                "asset_symbol": asset_symbol.upper(),
                "quantity": qty,
                "market_price": mkt,
                "average_cost": avg,
                "market_value": mv,
                "cost_basis": cb,
                "unrealized_pnl": round(mv - cb, 8),
                "at": _now(),
            },
        )

    def revalue(self, *, asset_symbol: str, new_price: float, quantity: float) -> dict[str, Any]:
        if float(new_price) < 0 or float(quantity) < 0:
            raise ValidationError("new_price and quantity must be non-negative")
        rid = _id("da_rev")
        return self.store.da_revaluations.save(
            rid,
            {
                "revaluation_id": rid,
                "asset_symbol": asset_symbol.upper(),
                "new_price": float(new_price),
                "quantity": float(quantity),
                "fair_value": round(float(new_price) * float(quantity), 8),
                "at": _now(),
            },
        )

    def portfolio_valuation(self, *, holdings: list[dict[str, Any]]) -> dict[str, Any]:
        if not holdings:
            raise ValidationError("holdings required")
        rows = []
        total = 0.0
        for h in holdings:
            qty = float(h.get("quantity", 0) or 0)
            price = float(h.get("price", 0) or 0)
            value = round(qty * price, 8)
            total += value
            rows.append(
                {
                    "symbol": str(h.get("symbol", "")).upper(),
                    "quantity": qty,
                    "price": price,
                    "value": value,
                }
            )
        pid = _id("da_pval")
        return self.store.da_portfolio_vals.save(
            pid,
            {
                "valuation_id": pid,
                "holdings": rows,
                "total_value": round(total, 8),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "ledger": self.store.da_ledger.count(),
            "cost_basis": self.store.da_cost_basis.count(),
            "realized": self.store.da_realized.count(),
            "unrealized": self.store.da_unrealized.count(),
            "revaluations": self.store.da_revaluations.count(),
            "portfolio_valuations": self.store.da_portfolio_vals.count(),
        }
