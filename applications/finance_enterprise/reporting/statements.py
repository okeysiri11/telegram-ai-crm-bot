"""Financial statements — BS, P&L, cash flow, trial balance, GL, equity."""

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


class FinancialStatements:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.statement_types = list(DEFAULT_CONFIG.rpt_statement_types)

    def generate(
        self,
        *,
        statement_type: str,
        period: str,
        entity_ref: str = "",
        lines: list[dict[str, Any]] | None = None,
        totals: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        st = statement_type.lower().strip()
        if st not in self.statement_types:
            raise ValidationError(f"statement_type must be one of {self.statement_types}")
        if not period:
            raise ValidationError("period required")
        sid = _id("rpt_stmt")
        default_totals = {
            "balance_sheet": {"assets": 0.0, "liabilities": 0.0, "equity": 0.0},
            "profit_loss": {"revenue": 0.0, "expenses": 0.0, "net_income": 0.0},
            "cash_flow": {"operating": 0.0, "investing": 0.0, "financing": 0.0, "net_change": 0.0},
            "trial_balance": {"debits": 0.0, "credits": 0.0},
            "general_ledger": {"entries": 0.0, "balance": 0.0},
            "equity": {"opening": 0.0, "net_income": 0.0, "dividends": 0.0, "closing": 0.0},
        }.get(st, {})
        return self.store.rpt_statements.save(
            sid,
            {
                "statement_id": sid,
                "statement_type": st,
                "period": period,
                "entity_ref": entity_ref,
                "lines": lines or [],
                "totals": totals or default_totals,
                "status": "issued",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "statements": self.store.rpt_statements.count(),
            "types": self.statement_types,
        }
