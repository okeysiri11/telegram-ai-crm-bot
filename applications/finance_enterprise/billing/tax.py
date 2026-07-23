"""Tax engine — registry, VAT, sales tax, rules, reporting."""

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


class TaxEngine:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def register_tax(
        self, *, code: str, name: str, rate: float, tax_type: str = "vat"
    ) -> dict[str, Any]:
        if not code or not name:
            raise ValidationError("code and name required")
        if float(rate) < 0:
            raise ValidationError("rate must be non-negative")
        tid = _id("bil_tax")
        return self.store.bil_taxes.save(
            tid,
            {
                "tax_id": tid,
                "code": code.upper(),
                "name": name,
                "rate": float(rate),
                "tax_type": tax_type.lower(),
                "created_at": _now(),
            },
        )

    def calculate(
        self, *, taxable_amount: float, rate: float, tax_type: str = "vat"
    ) -> dict[str, Any]:
        base = float(taxable_amount)
        r = float(rate)
        if base < 0 or r < 0:
            raise ValidationError("taxable_amount and rate must be non-negative")
        tax = round(base * r, 6)
        cid = _id("bil_tcalc")
        return self.store.bil_tax_calcs.save(
            cid,
            {
                "calculation_id": cid,
                "tax_type": tax_type.lower(),
                "taxable_amount": base,
                "rate": r,
                "tax_amount": tax,
                "gross": round(base + tax, 6),
                "at": _now(),
            },
        )

    def add_rule(self, *, code: str, jurisdiction: str, rate: float, detail: str = "") -> dict[str, Any]:
        if not code or not jurisdiction:
            raise ValidationError("code and jurisdiction required")
        rid = _id("bil_trule")
        return self.store.bil_tax_rules.save(
            rid,
            {
                "rule_id": rid,
                "code": code.upper(),
                "jurisdiction": jurisdiction,
                "rate": float(rate),
                "detail": detail,
                "at": _now(),
            },
        )

    def report(self, *, period: str = "2026-Q3") -> dict[str, Any]:
        calcs = self.store.bil_tax_calcs.list_all()
        total_tax = sum(float(c.get("tax_amount", 0)) for c in calcs)
        rid = _id("bil_trep")
        return self.store.bil_tax_reports.save(
            rid,
            {
                "report_id": rid,
                "period": period,
                "calculation_count": len(calcs),
                "total_tax": total_tax,
                "at": _now(),
            },
        )

    def summary(self) -> dict[str, Any]:
        sid = _id("bil_tsum")
        return self.store.bil_tax_summaries.save(
            sid,
            {
                "summary_id": sid,
                "taxes": self.store.bil_taxes.count(),
                "rules": self.store.bil_tax_rules.count(),
                "calculations": self.store.bil_tax_calcs.count(),
                "reports": self.store.bil_tax_reports.count(),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "taxes": self.store.bil_taxes.count(),
            "rules": self.store.bil_tax_rules.count(),
            "calculations": self.store.bil_tax_calcs.count(),
            "reports": self.store.bil_tax_reports.count(),
            "summaries": self.store.bil_tax_summaries.count(),
        }
