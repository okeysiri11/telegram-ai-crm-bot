# Revenue + Cost + Profitability engines.

from __future__ import annotations

from applications.port_erp.finance.models import ExpenseRecord
from applications.port_erp.shared.exceptions import ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class RevenueEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def total_revenue(self, *, company_id: str | None = None) -> float:
        invoices = self._store.commercial_invoices.list_all()
        if company_id:
            invoices = [i for i in invoices if i.company_id == company_id]
        return round(sum(i.amount_paid for i in invoices), 2)

    def by_customer(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for inv in self._store.commercial_invoices.list_all():
            result[inv.customer_id] = round(result.get(inv.customer_id, 0.0) + inv.amount_paid, 2)
        return result

    def by_terminal(self) -> dict[str, float]:
        # Approximate from tariff terminal_id on charge lines
        result: dict[str, float] = {}
        tariffs = {t.tariff_id: t for t in self._store.commercial_tariffs.list_all()}
        for inv in self._store.commercial_invoices.list_all():
            for line in inv.lines:
                tariff = tariffs.get(line.tariff_id)
                key = tariff.terminal_id if tariff and tariff.terminal_id else "unallocated"
                result[key] = round(result.get(key, 0.0) + line.amount, 2)
        return result

    def by_berth(self) -> dict[str, float]:
        # Berth fees aggregated as fee_type berth_fees
        total = 0.0
        for inv in self._store.commercial_invoices.list_all():
            for line in inv.lines:
                if line.fee_type.value == "berth_fees":
                    total += line.amount
        return {"berth_fees": round(total, 2)}

    def forecast(self, *, months: int = 3) -> dict:
        current = self.total_revenue()
        monthly = current  # simple baseline
        return {
            "baseline_monthly": monthly,
            "months": months,
            "forecast_total": round(monthly * months * 1.05, 2),
            "growth_rate": 0.05,
        }


class CostEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def record(self, expense: ExpenseRecord) -> ExpenseRecord:
        if expense.amount < 0:
            raise ValidationError("amount must be non-negative")
        return self._store.expense_records.save(expense.expense_id, expense)

    def total_cost(self, *, company_id: str | None = None) -> float:
        items = self._store.expense_records.list_all()
        if company_id:
            items = [e for e in items if e.company_id == company_id]
        return round(sum(e.amount for e in items), 2)

    def by_cost_center(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for exp in self._store.expense_records.list_all():
            key = exp.cost_center or "general"
            result[key] = round(result.get(key, 0.0) + exp.amount, 2)
        return result


class ProfitabilityEngine:
    def __init__(
        self,
        revenue: RevenueEngine | None = None,
        costs: CostEngine | None = None,
    ) -> None:
        self._revenue = revenue or revenue_engine
        self._costs = costs or cost_engine

    def summary(self, *, company_id: str | None = None) -> dict:
        rev = self._revenue.total_revenue(company_id=company_id)
        cost = self._costs.total_cost(company_id=company_id)
        profit = round(rev - cost, 2)
        margin = round(profit / rev, 4) if rev else 0.0
        return {
            "revenue": rev,
            "expenses": cost,
            "profit": profit,
            "margin": margin,
            "revenue_per_customer": self._revenue.by_customer(),
            "revenue_per_terminal": self._revenue.by_terminal(),
            "revenue_per_berth": self._revenue.by_berth(),
            "forecast": self._revenue.forecast(),
            "cost_by_center": self._costs.by_cost_center(),
        }


revenue_engine = RevenueEngine()
cost_engine = CostEngine()
profitability_engine = ProfitabilityEngine(revenue=revenue_engine, costs=cost_engine)
