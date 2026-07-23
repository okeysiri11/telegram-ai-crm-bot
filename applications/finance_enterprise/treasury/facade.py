"""Treasury Suite facade — Sprint 18.3."""

from __future__ import annotations

from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store
from applications.finance_enterprise.treasury.ai_treasury import AITreasuryIntelligence
from applications.finance_enterprise.treasury.budgets import BudgetManagement
from applications.finance_enterprise.treasury.forecasting import Forecasting
from applications.finance_enterprise.treasury.planning import FinancialPlanning
from applications.finance_enterprise.treasury.reconciliation import BankReconciliation
from applications.finance_enterprise.treasury.services import TreasuryDashboard, TreasuryKnowledge
from applications.finance_enterprise.treasury.treasury_mgmt import TreasuryManagement
from applications.finance_enterprise.treasury.variance import VarianceAnalysis


class TreasurySuite:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.treasury = TreasuryManagement(self.store)
        self.reconciliation = BankReconciliation(self.store)
        self.budgets = BudgetManagement(self.store)
        self.planning = FinancialPlanning(self.store)
        self.forecasting = Forecasting(self.store)
        self.variance = VarianceAnalysis(self.store)
        self.ai = AITreasuryIntelligence(self.store)
        self.knowledge = TreasuryKnowledge(self.store)
        self.dashboard = TreasuryDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        entity = self.treasury.register_entity(name="Bidex Treasury")
        pool = self.treasury.create_pool(name="Group Cash Pool", balance=2_500_000)
        liq = self.treasury.monitor_liquidity(pool_id=pool["pool_id"], available=2_000_000, committed=400_000)
        pos = self.treasury.cash_position(label="Operating cash", amount=1_200_000)
        ic = self.treasury.intercompany_funding(
            from_entity="HQ", to_entity="Subsidiary EU", amount=250_000
        )
        op = self.treasury.operate(
            operation="sweep", amount=100_000, pool_id=pool["pool_id"], detail="daily sweep"
        )

        stmt = self.reconciliation.import_statement(
            account_ref="BANK-001",
            period="2026-07",
            lines=[
                {"memo": "inflow", "amount": 50000, "external_id": "TXN-1"},
                {"memo": "outflow", "amount": -12000, "external_id": "TXN-2"},
            ],
        )
        matches = self.reconciliation.auto_match(
            statement_id=stmt["statement_id"], book_refs=["JE-1", "JE-2"]
        )
        manual = self.reconciliation.manual_reconcile(
            statement_id=stmt["statement_id"], line_index=0, book_ref="JE-1-ADJ"
        )
        exc = self.reconciliation.exception(
            statement_id=stmt["statement_id"], reason="unmatched fee", severity="low"
        )
        rrep = self.reconciliation.report(statement_id=stmt["statement_id"])
        aud = self.reconciliation.audit(action="reconcile.bootstrap", actor="controller")

        dept = self.budgets.create_budget(
            name="Finance Dept 2026", budget_type="department", amount=800_000, owner_ref="FIN"
        )
        proj = self.budgets.create_budget(
            name="ERP Upgrade", budget_type="project", amount=350_000, owner_ref="IT"
        )
        cc = self.budgets.create_budget(
            name="CC-OPS", budget_type="cost_center", amount=120_000, owner_ref="OPS"
        )
        bapr = self.budgets.approve(budget_id=dept["budget_id"], approver="cfo")
        brev = self.budgets.revise(budget_id=proj["budget_id"], new_amount=375_000, reason="scope")

        ws = self.planning.create_workspace(name="FY2026 Plan")
        rev = self.planning.add_plan(
            workspace_id=ws["workspace_id"], plan_type="revenue", amount=12_000_000
        )
        exp = self.planning.add_plan(
            workspace_id=ws["workspace_id"], plan_type="expense", amount=9_500_000
        )
        capex = self.planning.add_plan(
            workspace_id=ws["workspace_id"], plan_type="capex", amount=1_000_000
        )
        invest = self.planning.add_plan(
            workspace_id=ws["workspace_id"], plan_type="investment", amount=500_000
        )
        wc = self.planning.add_plan(
            workspace_id=ws["workspace_id"], plan_type="working_capital", amount=750_000
        )

        cash_fc = self.forecasting.forecast(kind="cash_flow", horizon_days=90, projected=1_800_000)
        rev_fc = self.forecasting.forecast(kind="revenue", horizon_days=180, projected=12_500_000)
        exp_fc = self.forecasting.forecast(kind="expense", horizon_days=180, projected=9_800_000)
        liq_fc = self.forecasting.forecast(kind="liquidity", horizon_days=60, projected=1_600_000)
        scn = self.forecasting.scenario(name="Upside", base_amount=12_000_000, uplift_pct=8)
        sens = self.forecasting.sensitivity(variable="revenue", low=11e6, base=12e6, high=13e6)

        var_ba = self.variance.analyze(
            variance_type="budget_vs_actual", budget=800_000, actual=780_000, subject="Finance"
        )
        var_rev = self.variance.analyze(
            variance_type="revenue", budget=3_000_000, actual=3_100_000, subject="Q3"
        )
        var_exp = self.variance.analyze(
            variance_type="expense", budget=2_400_000, actual=2_450_000, subject="Q3"
        )
        var_cf = self.variance.analyze(
            variance_type="cash_flow", budget=500_000, actual=480_000, subject="July"
        )
        var_dept = self.variance.analyze(
            variance_type="department", budget=800_000, actual=780_000, subject="Finance"
        )
        kpi = self.variance.kpi(name="liquidity_ratio", value=1.35, target=1.2, unit="x")

        ai_dev = self.ai.insight(insight_type="budget_deviation", subject=dept["budget_id"], score=0.4)
        ai_liq = self.ai.insight(insight_type="liquidity_risk", subject=pool["pool_id"], score=0.35)
        ai_opt = self.ai.insight(insight_type="forecast_optimization", subject=cash_fc["forecast_id"])
        ai_anom = self.ai.insight(insight_type="financial_anomaly", subject=stmt["statement_id"], score=0.22)
        ai_cap = self.ai.insight(insight_type="capital_allocation", subject="FY2026", score=0.7)
        ai_nl = self.ai.nl_summary(audience="cfo")

        self.knowledge.publish(base="treasury", key=pool["pool_id"], payload={"name": pool["name"]})
        self.knowledge.publish(base="budget", key=dept["budget_id"], payload={"amount": dept["amount"]})
        self.knowledge.publish(base="forecast", key=cash_fc["forecast_id"], payload={"kind": "cash_flow"})
        self.knowledge.publish(base="liquidity", key=liq["liquidity_id"], payload={"net": liq["net"]})
        self.knowledge.publish(base="planning", key=ws["workspace_id"], payload={"name": ws["name"]})

        dash_t = self.dashboard.render(dashboard_type="treasury")
        dash_b = self.dashboard.render(dashboard_type="budget")
        dash_f = self.dashboard.render(dashboard_type="forecast")
        dash_l = self.dashboard.render(dashboard_type="liquidity")
        dash_p = self.dashboard.render(dashboard_type="planning")

        return {
            "bootstrap": True,
            "entity_id": entity["entity_id"],
            "pool_id": pool["pool_id"],
            "liquidity_id": liq["liquidity_id"],
            "position_id": pos["position_id"],
            "intercompany_id": ic["funding_id"],
            "operation_id": op["operation_id"],
            "statement_id": stmt["statement_id"],
            "match_count": matches["match_count"],
            "manual_match_id": manual["match_id"],
            "exception_id": exc["exception_id"],
            "recon_report_id": rrep["report_id"],
            "audit_id": aud["audit_id"],
            "dept_budget_id": dept["budget_id"],
            "project_budget_id": proj["budget_id"],
            "cost_center_budget_id": cc["budget_id"],
            "budget_approval_id": bapr["approval_id"],
            "budget_revision_id": brev["revision_id"],
            "workspace_id": ws["workspace_id"],
            "revenue_plan_id": rev["plan_id"],
            "expense_plan_id": exp["plan_id"],
            "capex_plan_id": capex["plan_id"],
            "investment_plan_id": invest["plan_id"],
            "wc_plan_id": wc["plan_id"],
            "cash_forecast_id": cash_fc["forecast_id"],
            "revenue_forecast_id": rev_fc["forecast_id"],
            "expense_forecast_id": exp_fc["forecast_id"],
            "liquidity_forecast_id": liq_fc["forecast_id"],
            "scenario_id": scn["scenario_id"],
            "sensitivity_id": sens["sensitivity_id"],
            "variance_ba_id": var_ba["variance_id"],
            "variance_rev_id": var_rev["variance_id"],
            "variance_exp_id": var_exp["variance_id"],
            "variance_cf_id": var_cf["variance_id"],
            "variance_dept_id": var_dept["variance_id"],
            "kpi_id": kpi["kpi_id"],
            "ai_deviation_id": ai_dev["insight_id"],
            "ai_liquidity_id": ai_liq["insight_id"],
            "ai_optimization_id": ai_opt["insight_id"],
            "ai_anomaly_id": ai_anom["insight_id"],
            "ai_capital_id": ai_cap["insight_id"],
            "ai_nl_id": ai_nl["insight_id"],
            "dashboard_treasury_id": dash_t["dashboard_id"],
            "dashboard_budget_id": dash_b["dashboard_id"],
            "dashboard_forecast_id": dash_f["dashboard_id"],
            "dashboard_liquidity_id": dash_l["dashboard_id"],
            "dashboard_planning_id": dash_p["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "treasury": self.treasury.status(),
            "reconciliation": self.reconciliation.status(),
            "budgets": self.budgets.status(),
            "planning": self.planning.status(),
            "forecasting": self.forecasting.status(),
            "variance": self.variance.status(),
            "ai": self.ai.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


treasury = TreasurySuite()
