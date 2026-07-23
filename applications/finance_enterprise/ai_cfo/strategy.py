"""Strategic financial planning — capital, investment, budget, growth, expansion."""

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


class StrategicPlanning:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.plan_types = list(DEFAULT_CONFIG.cfo_strategy_types)

    def plan(
        self,
        *,
        plan_type: str,
        label: str,
        amount: float = 0.0,
        priority: int = 1,
        detail: str = "",
    ) -> dict[str, Any]:
        pt = plan_type.lower().strip()
        if pt not in self.plan_types:
            raise ValidationError(f"plan_type must be one of {self.plan_types}")
        if not label:
            raise ValidationError("label required")
        pid = _id("cfo_str")
        return self.store.cfo_strategies.save(
            pid,
            {
                "strategy_id": pid,
                "plan_type": pt,
                "label": label,
                "amount": float(amount),
                "priority": int(priority),
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "strategies": self.store.cfo_strategies.count(),
            "types": self.plan_types,
        }
