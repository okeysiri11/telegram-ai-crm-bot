"""Treasury management — pools, liquidity, positions, intercompany, operations."""

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


class TreasuryManagement:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def register_entity(self, *, name: str, entity_type: str = "treasury_unit") -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        eid = _id("tr_ent")
        return self.store.tr_entities.save(
            eid,
            {
                "entity_id": eid,
                "name": name,
                "entity_type": entity_type,
                "created_at": _now(),
            },
        )

    def create_pool(
        self, *, name: str, currency: str = "USD", balance: float = 0.0
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("pool name required")
        pid = _id("tr_pool")
        return self.store.tr_pools.save(
            pid,
            {
                "pool_id": pid,
                "name": name,
                "currency": currency.upper(),
                "balance": float(balance),
                "created_at": _now(),
            },
        )

    def monitor_liquidity(
        self, *, pool_id: str, available: float, committed: float = 0.0
    ) -> dict[str, Any]:
        if self.store.tr_pools.get(pool_id) is None:
            raise NotFoundError("cash_pool", pool_id)
        lid = _id("tr_liq")
        avail = float(available)
        comm = float(committed)
        return self.store.tr_liquidity.save(
            lid,
            {
                "liquidity_id": lid,
                "pool_id": pool_id,
                "available": avail,
                "committed": comm,
                "net": round(avail - comm, 6),
                "at": _now(),
            },
        )

    def cash_position(
        self, *, label: str, amount: float, currency: str = "USD"
    ) -> dict[str, Any]:
        if not label:
            raise ValidationError("label required")
        cid = _id("tr_pos")
        return self.store.tr_positions.save(
            cid,
            {
                "position_id": cid,
                "label": label,
                "amount": float(amount),
                "currency": currency.upper(),
                "at": _now(),
            },
        )

    def intercompany_funding(
        self,
        *,
        from_entity: str,
        to_entity: str,
        amount: float,
        currency: str = "USD",
    ) -> dict[str, Any]:
        if not from_entity or not to_entity:
            raise ValidationError("from_entity and to_entity required")
        if float(amount) <= 0:
            raise ValidationError("amount must be positive")
        fid = _id("tr_ic")
        return self.store.tr_intercompany.save(
            fid,
            {
                "funding_id": fid,
                "from_entity": from_entity,
                "to_entity": to_entity,
                "amount": float(amount),
                "currency": currency.upper(),
                "at": _now(),
            },
        )

    def operate(
        self, *, operation: str, amount: float, pool_id: str = "", detail: str = ""
    ) -> dict[str, Any]:
        if not operation:
            raise ValidationError("operation required")
        if float(amount) <= 0:
            raise ValidationError("amount must be positive")
        oid = _id("tr_op")
        return self.store.tr_operations.save(
            oid,
            {
                "operation_id": oid,
                "operation": operation,
                "amount": float(amount),
                "pool_id": pool_id,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entities": self.store.tr_entities.count(),
            "pools": self.store.tr_pools.count(),
            "liquidity": self.store.tr_liquidity.count(),
            "positions": self.store.tr_positions.count(),
            "intercompany": self.store.tr_intercompany.count(),
            "operations": self.store.tr_operations.count(),
        }
