"""Financial modeling — ROI, NPV, IRR, break-even, sensitivity, what-if."""

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


class FinancialModeling:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.model_types = list(DEFAULT_CONFIG.cfo_model_types)

    def model(
        self,
        *,
        model_type: str,
        label: str,
        inputs: dict[str, float] | None = None,
        result: float = 0.0,
        detail: str = "",
    ) -> dict[str, Any]:
        mt = model_type.lower().strip()
        if mt not in self.model_types:
            raise ValidationError(f"model_type must be one of {self.model_types}")
        if not label:
            raise ValidationError("label required")
        inp = inputs or {}
        computed = float(result)
        if mt == "roi" and not result:
            invest = float(inp.get("investment", 0) or 0)
            gain = float(inp.get("gain", 0) or 0)
            computed = round((gain - invest) / invest * 100, 4) if invest else 0.0
        elif mt == "npv" and not result:
            invest = float(inp.get("investment", 0) or 0)
            pv = float(inp.get("present_value", 0) or 0)
            computed = round(pv - invest, 8)
        elif mt == "break_even" and not result:
            fixed = float(inp.get("fixed_costs", 0) or 0)
            price = float(inp.get("price", 0) or 0)
            variable = float(inp.get("variable_cost", 0) or 0)
            contrib = price - variable
            computed = round(fixed / contrib, 4) if contrib else 0.0
        mid = _id("cfo_mdl")
        return self.store.cfo_models.save(
            mid,
            {
                "model_id": mid,
                "model_type": mt,
                "label": label,
                "inputs": inp,
                "result": computed,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"models": self.store.cfo_models.count(), "types": self.model_types}
