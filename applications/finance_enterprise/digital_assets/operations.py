"""Digital asset treasury operations — deposits, withdrawals, transfers, OTC, rebalance."""

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


class DigitalAssetOperations:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.op_types = list(DEFAULT_CONFIG.da_operation_types)

    def operate(
        self,
        *,
        operation: str,
        asset_symbol: str,
        amount: float,
        from_ref: str = "",
        to_ref: str = "",
        detail: str = "",
    ) -> dict[str, Any]:
        op = operation.lower().strip()
        if op not in self.op_types:
            raise ValidationError(f"operation must be one of {self.op_types}")
        if not asset_symbol:
            raise ValidationError("asset_symbol required")
        amt = float(amount)
        if amt <= 0:
            raise ValidationError("amount must be positive")
        oid = _id("da_op")
        return self.store.da_operations.save(
            oid,
            {
                "operation_id": oid,
                "operation": op,
                "asset_symbol": asset_symbol.upper(),
                "amount": amt,
                "from_ref": from_ref,
                "to_ref": to_ref,
                "detail": detail,
                "status": "completed",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"operations": self.store.da_operations.count(), "types": self.op_types}
