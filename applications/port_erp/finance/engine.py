# Finance Engine — cash flow, multi-company commercial facade core.

from __future__ import annotations

from applications.port_erp.accounting.engine import AccountingEngine, accounting_engine
from applications.port_erp.budget.engine import BudgetEngine, budget_engine
from applications.port_erp.finance.models import CostCenter, ExpenseRecord
from applications.port_erp.profitability.engine import (
    CostEngine,
    ProfitabilityEngine,
    RevenueEngine,
    cost_engine,
    profitability_engine,
    revenue_engine,
)
from applications.port_erp.shared.store import PortStore, port_store


class FinanceEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        revenue: RevenueEngine | None = None,
        costs: CostEngine | None = None,
        profitability: ProfitabilityEngine | None = None,
        accounting: AccountingEngine | None = None,
        budgets: BudgetEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self.revenue = revenue or revenue_engine
        self.costs = costs or cost_engine
        self.profitability = profitability or profitability_engine
        self.accounting = accounting or accounting_engine
        self.budgets = budgets or budget_engine

    def cash_flow(self, *, company_id: str | None = None) -> dict:
        inflow = self.revenue.total_revenue(company_id=company_id)
        outflow = self.costs.total_cost(company_id=company_id)
        return {
            "inflow": inflow,
            "outflow": outflow,
            "net": round(inflow - outflow, 2),
            "receivables": self.accounting.receivables(),
            "payables": self.accounting.payables(),
        }

    def record_expense(self, expense: ExpenseRecord) -> ExpenseRecord:
        return self.costs.record(expense)

    def ensure_cost_center(self, center: CostCenter) -> CostCenter:
        return self.budgets.create_cost_center(center)

    def companies_snapshot(self) -> list[dict]:
        company_ids = {
            i.company_id for i in self._store.commercial_invoices.list_all() if i.company_id
        } | {e.company_id for e in self._store.expense_records.list_all() if e.company_id}
        if not company_ids:
            company_ids = {""}
        return [
            {
                "company_id": cid or "default",
                "profitability": self.profitability.summary(company_id=cid or None),
                "cash_flow": self.cash_flow(company_id=cid or None),
            }
            for cid in sorted(company_ids)
        ]


finance_engine = FinanceEngine()
