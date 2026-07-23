"""AI CFO Suite facade — Sprint 18.6."""

from __future__ import annotations

from typing import Any

from applications.finance_enterprise.ai_cfo.decisions import DecisionSupport
from applications.finance_enterprise.ai_cfo.executive import ExecutiveReporting
from applications.finance_enterprise.ai_cfo.modeling import FinancialModeling
from applications.finance_enterprise.ai_cfo.performance import PerformanceAnalysis
from applications.finance_enterprise.ai_cfo.risk import RiskIntelligence
from applications.finance_enterprise.ai_cfo.services import AICFODashboard, AICFOKnowledge
from applications.finance_enterprise.ai_cfo.strategy import StrategicPlanning
from applications.finance_enterprise.ai_cfo.workspace import AICFOWorkspace
from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


class AICFOSuite:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.workspace = AICFOWorkspace(self.store)
        self.performance = PerformanceAnalysis(self.store)
        self.strategy = StrategicPlanning(self.store)
        self.modeling = FinancialModeling(self.store)
        self.risk = RiskIntelligence(self.store)
        self.decisions = DecisionSupport(self.store)
        self.executive = ExecutiveReporting(self.store)
        self.knowledge = AICFOKnowledge(self.store)
        self.dashboard = AICFODashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        ws = self.workspace.open_workspace(label="Executive Finance Desk", owner="cfo")
        chat = self.workspace.chat(
            workspace_id=ws["workspace_id"],
            message="Summarize Q2 liquidity position",
            role="executive_assistant",
            context="treasury",
        )
        qa = self.workspace.ask(
            workspace_id=ws["workspace_id"],
            question="What is our current gross margin trend?",
        )

        rev = self.performance.analyze(
            analysis_type="revenue", subject="FY2026", value=1_200_000, prior=1_050_000
        )
        exp = self.performance.analyze(
            analysis_type="expense", subject="FY2026", value=800_000, prior=780_000
        )
        prof = self.performance.analyze(
            analysis_type="profitability", subject="FY2026", value=400_000, prior=320_000
        )
        mar = self.performance.analyze(
            analysis_type="margin", subject="Gross", value=42.5, prior=40.0
        )
        cost = self.performance.analyze(
            analysis_type="cost_structure", subject="Opex mix", value=0.55, prior=0.58
        )
        wc = self.performance.analyze(
            analysis_type="working_capital", subject="Group", value=850_000, prior=780_000
        )

        cap = self.strategy.plan(
            plan_type="capital_allocation", label="Growth vs Yield", amount=2_000_000, priority=1
        )
        inv = self.strategy.plan(
            plan_type="investment_analysis", label="Platform Capex", amount=500_000, priority=2
        )
        bud = self.strategy.plan(
            plan_type="budget_optimization", label="Opex trim 5%", amount=40_000, priority=2
        )
        res = self.strategy.plan(
            plan_type="resource_allocation", label="Headcount plan", amount=120, priority=3
        )
        growth = self.strategy.plan(
            plan_type="growth_planning", label="Enterprise ARR", amount=1_500_000, priority=1
        )
        expn = self.strategy.plan(
            plan_type="expansion_scenario", label="APAC entry", amount=750_000, priority=3
        )

        roi = self.modeling.model(
            model_type="roi",
            label="Platform ROI",
            inputs={"investment": 500_000, "gain": 750_000},
        )
        npv = self.modeling.model(
            model_type="npv",
            label="Expansion NPV",
            inputs={"investment": 750_000, "present_value": 920_000},
        )
        irr = self.modeling.model(
            model_type="irr", label="Capex IRR", result=0.18, detail="estimated IRR 18%"
        )
        be = self.modeling.model(
            model_type="break_even",
            label="Product BE",
            inputs={"fixed_costs": 100_000, "price": 50, "variable_cost": 20},
        )
        sens = self.modeling.model(
            model_type="sensitivity",
            label="Volume shock -10%",
            inputs={"base": 1_200_000, "shock_pct": -10},
            result=-120_000,
        )
        whatif = self.modeling.model(
            model_type="what_if",
            label="Price +5%",
            inputs={"base_revenue": 1_200_000, "uplift_pct": 5},
            result=60_000,
        )

        r_liq = self.risk.assess(
            risk_type="liquidity", subject="30-day runway", score=0.35, mitigation="Maintain cash buffer"
        )
        r_cred = self.risk.assess(
            risk_type="credit", subject="AR aging", score=0.45, mitigation="Tighten credit terms"
        )
        r_cf = self.risk.assess(
            risk_type="cash_flow", subject="Seasonality", score=0.5, mitigation="Stagger payables"
        )
        r_bud = self.risk.assess(
            risk_type="budget_deviation", subject="Marketing", score=0.62, mitigation="Reallocate spend"
        )
        r_stab = self.risk.assess(
            risk_type="financial_stability", subject="Group", score=0.28, mitigation="Continue deleveraging"
        )
        r_mit = self.risk.assess(
            risk_type="mitigation", subject="Portfolio hedges", score=0.4, mitigation="Extend FX hedges"
        )

        rec_exe = self.decisions.recommend(
            recommendation_type="executive", subject="Prioritize cash conversion", priority=1, score=0.9
        )
        rec_cost = self.decisions.recommend(
            recommendation_type="cost_optimization", subject="Cloud spend", priority=2, score=0.8
        )
        rec_rev = self.decisions.recommend(
            recommendation_type="revenue_improvement", subject="Upsell Enterprise", priority=1, score=0.85
        )
        rec_inv = self.decisions.recommend(
            recommendation_type="investment", subject="AI automation", priority=2, score=0.78
        )
        rec_cash = self.decisions.recommend(
            recommendation_type="cash_management", subject="Sweep idle cash", priority=1, score=0.88
        )
        rec_rank = self.decisions.recommend(
            recommendation_type="strategic_priority", subject="Ranked FY priorities", priority=1, score=0.92
        )

        daily = self.executive.report(report_type="daily_briefing", audience="cfo", period="2026-07-23")
        weekly = self.executive.report(report_type="weekly_summary", audience="finance_leads", period="2026-W30")
        monthly = self.executive.report(report_type="monthly_executive", audience="exco", period="2026-07")
        board = self.executive.report(report_type="board", audience="board", period="2026-Q2")
        nl = self.executive.report(
            report_type="nl_report",
            audience="ceo",
            narrative="Liquidity stable; recommend accelerating enterprise upsell and trimming cloud opex 5%.",
        )

        self.knowledge.publish(base="intelligence", key=ws["workspace_id"], payload={"label": ws["label"]})
        self.knowledge.publish(base="investment", key=inv["strategy_id"], payload={"label": inv["label"]})
        self.knowledge.publish(base="risk", key=r_liq["risk_id"], payload={"type": "liquidity"})
        self.knowledge.publish(base="strategy", key=cap["strategy_id"], payload={"type": "capital_allocation"})
        self.knowledge.publish(base="recommendation", key=rec_exe["recommendation_id"], payload={"priority": 1})

        dash_cfo = self.dashboard.render(dashboard_type="ai_cfo")
        dash_h = self.dashboard.render(dashboard_type="financial_health")
        dash_i = self.dashboard.render(dashboard_type="investment")
        dash_r = self.dashboard.render(dashboard_type="risk")
        dash_s = self.dashboard.render(dashboard_type="strategy")

        return {
            "bootstrap": True,
            "workspace_id": ws["workspace_id"],
            "chat_id": chat["conversation_id"],
            "qa_id": qa["conversation_id"],
            "revenue_id": rev["analysis_id"],
            "expense_id": exp["analysis_id"],
            "profitability_id": prof["analysis_id"],
            "margin_id": mar["analysis_id"],
            "cost_structure_id": cost["analysis_id"],
            "working_capital_id": wc["analysis_id"],
            "capital_allocation_id": cap["strategy_id"],
            "investment_id": inv["strategy_id"],
            "budget_optimization_id": bud["strategy_id"],
            "resource_allocation_id": res["strategy_id"],
            "growth_planning_id": growth["strategy_id"],
            "expansion_id": expn["strategy_id"],
            "roi_id": roi["model_id"],
            "npv_id": npv["model_id"],
            "irr_id": irr["model_id"],
            "break_even_id": be["model_id"],
            "sensitivity_id": sens["model_id"],
            "what_if_id": whatif["model_id"],
            "risk_liquidity_id": r_liq["risk_id"],
            "risk_credit_id": r_cred["risk_id"],
            "risk_cash_flow_id": r_cf["risk_id"],
            "risk_budget_id": r_bud["risk_id"],
            "risk_stability_id": r_stab["risk_id"],
            "risk_mitigation_id": r_mit["risk_id"],
            "rec_executive_id": rec_exe["recommendation_id"],
            "rec_cost_id": rec_cost["recommendation_id"],
            "rec_revenue_id": rec_rev["recommendation_id"],
            "rec_investment_id": rec_inv["recommendation_id"],
            "rec_cash_id": rec_cash["recommendation_id"],
            "rec_priority_id": rec_rank["recommendation_id"],
            "daily_briefing_id": daily["report_id"],
            "weekly_summary_id": weekly["report_id"],
            "monthly_executive_id": monthly["report_id"],
            "board_report_id": board["report_id"],
            "nl_report_id": nl["report_id"],
            "dashboard_ai_cfo_id": dash_cfo["dashboard_id"],
            "dashboard_health_id": dash_h["dashboard_id"],
            "dashboard_investment_id": dash_i["dashboard_id"],
            "dashboard_risk_id": dash_r["dashboard_id"],
            "dashboard_strategy_id": dash_s["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "workspace": self.workspace.status(),
            "performance": self.performance.status(),
            "strategy": self.strategy.status(),
            "modeling": self.modeling.status(),
            "risk": self.risk.status(),
            "decisions": self.decisions.status(),
            "executive": self.executive.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


ai_cfo = AICFOSuite()
