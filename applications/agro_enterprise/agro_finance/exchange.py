"""Commodity exchange and contract management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

TRADE_TYPES = ["spot", "forward", "auction"]
CONTRACT_TYPES = ["purchase", "sales", "export", "supplier", "buyer"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CommodityExchange:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_commodity(self, *, symbol: str, name: str, unit: str = "t") -> dict[str, Any]:
        if not symbol or not name:
            raise ValidationError("symbol and name required")
        cid = _id("af_cmd")
        return self.store.af_commodities.save(
            cid,
            {
                "commodity_id": cid,
                "symbol": symbol.upper(),
                "name": name,
                "unit": unit,
                "last_price": 0.0,
                "created_at": _now(),
            },
        )

    def place_order(
        self,
        *,
        commodity_id: str,
        side: str,
        trade_type: str = "spot",
        quantity: float,
        price: float,
        party: str = "",
    ) -> dict[str, Any]:
        cmd = self.store.af_commodities.get(commodity_id)
        if cmd is None:
            raise NotFoundError("commodity", commodity_id)
        if side not in ("buy", "sell"):
            raise ValidationError("side must be buy or sell")
        if trade_type not in TRADE_TYPES:
            raise ValidationError(f"trade_type must be one of {TRADE_TYPES}")
        oid = _id("af_ord")
        order = self.store.af_orders.save(
            oid,
            {
                "order_id": oid,
                "commodity_id": commodity_id,
                "symbol": cmd["symbol"],
                "side": side,
                "trade_type": trade_type,
                "quantity": float(quantity),
                "price": float(price),
                "party": party,
                "status": "open",
                "at": _now(),
            },
        )
        cmd["last_price"] = float(price)
        self.store.af_commodities.save(commodity_id, cmd)
        return order

    def execute_trade(self, *, buy_order_id: str, sell_order_id: str) -> dict[str, Any]:
        buy = self.store.af_orders.get(buy_order_id)
        sell = self.store.af_orders.get(sell_order_id)
        if buy is None:
            raise NotFoundError("order", buy_order_id)
        if sell is None:
            raise NotFoundError("order", sell_order_id)
        if buy["side"] != "buy" or sell["side"] != "sell":
            raise ValidationError("orders must be buy and sell")
        if buy["commodity_id"] != sell["commodity_id"]:
            raise ValidationError("commodity mismatch")
        qty = min(float(buy["quantity"]), float(sell["quantity"]))
        price = (float(buy["price"]) + float(sell["price"])) / 2
        tid = _id("af_trd")
        trade = self.store.af_trades.save(
            tid,
            {
                "trade_id": tid,
                "commodity_id": buy["commodity_id"],
                "symbol": buy["symbol"],
                "quantity": qty,
                "price": price,
                "buy_order_id": buy_order_id,
                "sell_order_id": sell_order_id,
                "at": _now(),
            },
        )
        buy["status"] = "filled"
        sell["status"] = "filled"
        self.store.af_orders.save(buy_order_id, buy)
        self.store.af_orders.save(sell_order_id, sell)
        return trade

    def market_depth(self, commodity_id: str) -> dict[str, Any]:
        if self.store.af_commodities.get(commodity_id) is None:
            raise NotFoundError("commodity", commodity_id)
        open_orders = [
            o
            for o in self.store.af_orders.list_all()
            if o.get("commodity_id") == commodity_id and o.get("status") == "open"
        ]
        bids = sorted(
            [o for o in open_orders if o["side"] == "buy"], key=lambda x: -float(x["price"])
        )[:5]
        asks = sorted(
            [o for o in open_orders if o["side"] == "sell"], key=lambda x: float(x["price"])
        )[:5]
        return {
            "commodity_id": commodity_id,
            "bids": bids,
            "asks": asks,
            "price_discovery": {
                "best_bid": float(bids[0]["price"]) if bids else None,
                "best_ask": float(asks[0]["price"]) if asks else None,
            },
        }

    def trade_history(self, commodity_id: str | None = None) -> list[dict[str, Any]]:
        trades = self.store.af_trades.list_all()
        if commodity_id:
            trades = [t for t in trades if t.get("commodity_id") == commodity_id]
        return trades

    def status(self) -> dict[str, Any]:
        return {
            "commodities": self.store.af_commodities.count(),
            "orders": self.store.af_orders.count(),
            "trades": self.store.af_trades.count(),
        }


class ContractManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def create_contract(
        self,
        *,
        contract_type: str,
        party: str,
        commodity: str,
        tons: float,
        value: float,
    ) -> dict[str, Any]:
        if contract_type not in CONTRACT_TYPES:
            raise ValidationError(f"contract_type must be one of {CONTRACT_TYPES}")
        if not party or not commodity:
            raise ValidationError("party and commodity required")
        cid = _id("af_ctr")
        return self.store.af_contracts.save(
            cid,
            {
                "contract_id": cid,
                "contract_type": contract_type,
                "party": party,
                "commodity": commodity,
                "tons": float(tons),
                "value": float(value),
                "status": "draft",
                "signed": False,
                "created_at": _now(),
            },
        )

    def advance_lifecycle(self, contract_id: str, *, status: str) -> dict[str, Any]:
        allowed = {"draft", "negotiating", "active", "fulfilled", "terminated"}
        if status not in allowed:
            raise ValidationError(f"status must be one of {sorted(allowed)}")
        ctr = self.store.af_contracts.get(contract_id)
        if ctr is None:
            raise NotFoundError("contract", contract_id)
        ctr["status"] = status
        ctr["updated_at"] = _now()
        return self.store.af_contracts.save(contract_id, ctr)

    def e_sign(self, contract_id: str, *, signer: str) -> dict[str, Any]:
        ctr = self.store.af_contracts.get(contract_id)
        if ctr is None:
            raise NotFoundError("contract", contract_id)
        ctr["signed"] = True
        ctr["signer"] = signer
        ctr["signed_at"] = _now()
        if ctr.get("status") == "draft":
            ctr["status"] = "active"
        return self.store.af_contracts.save(contract_id, ctr)

    def vault_document(self, *, contract_id: str, title: str, doc_type: str = "pdf") -> dict[str, Any]:
        if self.store.af_contracts.get(contract_id) is None:
            raise NotFoundError("contract", contract_id)
        did = _id("af_doc")
        return self.store.af_vault.save(
            did,
            {
                "document_id": did,
                "contract_id": contract_id,
                "title": title,
                "doc_type": doc_type,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "contracts": self.store.af_contracts.count(),
            "vault_docs": self.store.af_vault.count(),
        }
