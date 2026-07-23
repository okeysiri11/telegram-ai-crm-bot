"""Reporting Suite facade — Sprint 18.5."""

from __future__ import annotations

from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.reporting.ai_reporting import AIFinancialIntelligence
from applications.finance_enterprise.reporting.consolidation import EnterpriseConsolidation
from applications.finance_enterprise.reporting.forecasting import ReportingForecasting
from applications.finance_enterprise.reporting.intelligence import BusinessIntelligence
from applications.finance_enterprise.reporting.management import ManagementReporting
from applications.finance_enterprise.reporting.services import ReportingDashboard, ReportingKnowledge
from applications.finance_enterprise.reporting.statements import FinancialStatements
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


class ReportingSuite:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.statements = FinancialStatements(self.store)
        self.management = ManagementReporting(self.store)
        self.intelligence = BusinessIntelligence(self.store)
        self.consolidation = EnterpriseConsolidation(self.store)
        self.forecasting = ReportingForecasting(self.store)
        self.ai = AIFinancialIntelligence(self.store)
        self.knowledge = ReportingKnowledge(self.store)
        self.dashboard = ReportingDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        bs = self.statements.generate(
            statement_type="balance_sheet",
            period="2026-Q2",
            entity_ref="Bidex Holdings",
            totals={"assets": 5_000_000, "liabilities": 2_000_000, "equity": 3_000_000},
        )
        pl = self.statements.generate(
            statement_type="profit_loss",
            period="2026-Q2",
            totals={"revenue": 1_200_000, "expenses": 800_000, "net_income": 400_000},
        )
        cf = self.statements.generate(
            statement_type="cash_flow",
            period="2026-Q2",
            totals={"operating": 350_000, "investing": -80_000, "financing": -50_000, "net_change": 220_000},
        )
        tb = self.statements.generate(
            statement_type="trial_balance",
            period="2026-Q2",
            totals={"debits": 5_000_000, "credits": 5_000_000},
        )
        gl = self.statements.generate(
            statement_type="general_ledger",
            period="2026-Q2",
            lines=[{"account": "1000", "debit": 1000, "credit": 0}],
        )
        eq = self.statements.generate(
            statement_type="equity",
            period="2026-Q2",
            totals={"opening": 2_600_000, "net_income": 400_000, "dividends": 0, "closing": 3_000_000},
        )

        dept = self.management.generate(
            report_type="department", subject="Finance", period="2026-Q2", budget=200_000, actual=185_000
        )
        proj = self.management.generate(
            report_type="project_profitability",
            subject="Platform Rollout",
            period="2026-Q2",
            budget=500_000,
            actual=620_000,
        )
        cc = self.management.generate(
            report_type="cost_center", subject="CC-FIN", period="2026-Q2", budget=150_000, actual=148_000
        )
        bu = self.management.generate(
            report_type="business_unit", subject="Enterprise", period="2026-Q2", budget=2_000_000, actual=2_100_000
        )
        bva = self.management.generate(
            report_type="budget_vs_actual", subject="Group", period="2026-Q2", budget=3_000_000, actual=2_950_000
        )
        exe = self.management.generate(
            report_type="executive_summary", subject="Board Pack", period="2026-Q2", actual=400_000
        )

        kpi_m = self.intelligence.register_kpi(name="Gross Margin", kpi_type="margin", value=42.5)
        kpi_r = self.intelligence.register_kpi(name="Revenue Growth", kpi_type="revenue", value=12.0)
        an_rev = self.intelligence.analyze(
            analytic_type="revenue", subject="FY2026", value=1_200_000, prior=1_050_000
        )
        an_exp = self.intelligence.analyze(
            analytic_type="expense", subject="FY2026", value=800_000, prior=780_000
        )
        an_mar = self.intelligence.analyze(
            analytic_type="margin", subject="FY2026", value=33.3, prior=31.0
        )
        an_prof = self.intelligence.analyze(
            analytic_type="profitability", subject="FY2026", value=400_000, prior=320_000
        )
        an_tr = self.intelligence.analyze(
            analytic_type="trend", subject="Revenue", value=12.0, prior=8.0
        )
        an_var = self.intelligence.analyze(
            analytic_type="variance", subject="Opex", value=-15_000, prior=0
        )

        con_mc = self.consolidation.consolidate(
            consolidation_type="multi_company",
            label="Bidex Group",
            companies=["Holdings", "Ops", "Treasury"],
            amount=5_000_000,
            eliminated=200_000,
        )
        con_ic = self.consolidation.consolidate(
            consolidation_type="intercompany_elimination",
            label="IC Sales",
            amount=500_000,
            eliminated=500_000,
        )
        con_stmt = self.consolidation.consolidate(
            consolidation_type="consolidated_statements",
            label="Consolidated BS",
            amount=4_800_000,
        )
        con_grp = self.consolidation.consolidate(
            consolidation_type="group_performance",
            label="Group NI",
            amount=400_000,
        )
        con_xp = self.consolidation.consolidate(
            consolidation_type="cross_platform",
            label="Auto+Agro+Port Finance",
            amount=1_500_000,
        )

        fc_rev = self.forecasting.forecast(kind="revenue", horizon_days=90, projected=1_350_000)
        fc_prof = self.forecasting.forecast(kind="profit", horizon_days=90, projected=450_000)
        fc_cash = self.forecasting.forecast(kind="cash_flow", horizon_days=30, projected=250_000)
        fc_liq = self.forecasting.forecast(kind="liquidity", horizon_days=30, projected=2_000_000)
        scn = self.forecasting.scenario(name="Upside", base=400_000, uplift_pct=15)
        sens = self.forecasting.sensitivity(driver="volume", base=1_200_000, shock_pct=-10, impact=-80_000)

        ai_h = self.ai.health_score(subject="Bidex Group", score=0.84)
        ai_p = self.ai.insight(insight_type="profitability_recommendation", subject="Margins", score=0.75)
        ai_c = self.ai.insight(insight_type="cost_optimization", subject="Opex", score=0.7)
        ai_r = self.ai.insight(insight_type="revenue_growth", subject="Enterprise", score=0.78)
        ai_a = self.ai.insight(insight_type="anomaly", subject="Travel expense spike", score=0.91)
        ai_pred = self.ai.insight(insight_type="predictive", subject="Q3 NI", score=0.8)
        ai_nl = self.ai.nl_report(audience="board")

        self.knowledge.publish(base="reporting", key=bs["statement_id"], payload={"type": "balance_sheet"})
        self.knowledge.publish(base="kpi", key=kpi_m["kpi_id"], payload={"name": "Gross Margin"})
        self.knowledge.publish(base="report", key=exe["report_id"], payload={"type": "executive_summary"})
        self.knowledge.publish(base="forecast", key=fc_rev["forecast_id"], payload={"kind": "revenue"})
        self.knowledge.publish(base="analytics", key=an_rev["analytic_id"], payload={"type": "revenue"})

        dash_e = self.dashboard.render(dashboard_type="executive")
        dash_k = self.dashboard.render(dashboard_type="kpi")
        dash_p = self.dashboard.render(dashboard_type="profitability")
        dash_f = self.dashboard.render(dashboard_type="forecast")
        dash_bi = self.dashboard.render(dashboard_type="enterprise_bi")

        return {
            "bootstrap": True,
            "balance_sheet_id": bs["statement_id"],
            "profit_loss_id": pl["statement_id"],
            "cash_flow_id": cf["statement_id"],
            "trial_balance_id": tb["statement_id"],
            "general_ledger_id": gl["statement_id"],
            "equity_id": eq["statement_id"],
            "department_id": dept["report_id"],
            "project_id": proj["report_id"],
            "cost_center_id": cc["report_id"],
            "business_unit_id": bu["report_id"],
            "budget_vs_actual_id": bva["report_id"],
            "executive_summary_id": exe["report_id"],
            "kpi_margin_id": kpi_m["kpi_id"],
            "kpi_revenue_id": kpi_r["kpi_id"],
            "analytic_revenue_id": an_rev["analytic_id"],
            "analytic_expense_id": an_exp["analytic_id"],
            "analytic_margin_id": an_mar["analytic_id"],
            "analytic_profitability_id": an_prof["analytic_id"],
            "analytic_trend_id": an_tr["analytic_id"],
            "analytic_variance_id": an_var["analytic_id"],
            "consolidation_multi_id": con_mc["consolidation_id"],
            "consolidation_ic_id": con_ic["consolidation_id"],
            "consolidation_stmt_id": con_stmt["consolidation_id"],
            "consolidation_group_id": con_grp["consolidation_id"],
            "consolidation_cross_id": con_xp["consolidation_id"],
            "forecast_revenue_id": fc_rev["forecast_id"],
            "forecast_profit_id": fc_prof["forecast_id"],
            "forecast_cash_id": fc_cash["forecast_id"],
            "forecast_liquidity_id": fc_liq["forecast_id"],
            "scenario_id": scn["scenario_id"],
            "sensitivity_id": sens["sensitivity_id"],
            "ai_health_id": ai_h["insight_id"],
            "ai_profitability_id": ai_p["insight_id"],
            "ai_cost_id": ai_c["insight_id"],
            "ai_revenue_id": ai_r["insight_id"],
            "ai_anomaly_id": ai_a["insight_id"],
            "ai_predictive_id": ai_pred["insight_id"],
            "ai_nl_id": ai_nl["insight_id"],
            "dashboard_executive_id": dash_e["dashboard_id"],
            "dashboard_kpi_id": dash_k["dashboard_id"],
            "dashboard_profitability_id": dash_p["dashboard_id"],
            "dashboard_forecast_id": dash_f["dashboard_id"],
            "dashboard_enterprise_bi_id": dash_bi["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "statements": self.statements.status(),
            "management": self.management.status(),
            "intelligence": self.intelligence.status(),
            "consolidation": self.consolidation.status(),
            "forecasting": self.forecasting.status(),
            "ai": self.ai.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


reporting = ReportingSuite()
