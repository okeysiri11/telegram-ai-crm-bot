"""Executive Intelligence Suite facade — Sprint 17.7."""

from __future__ import annotations

from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.executive_intelligence.ai_executive import AIExecutiveIntelligence
from applications.legal_enterprise.executive_intelligence.alerts import AlertCenter
from applications.legal_enterprise.executive_intelligence.analytics import LegalAnalytics
from applications.legal_enterprise.executive_intelligence.decision_support import DecisionSupport
from applications.legal_enterprise.executive_intelligence.executive_dashboard import ExecutiveLegalDashboard
from applications.legal_enterprise.executive_intelligence.forecasting import RegulatoryForecasting
from applications.legal_enterprise.executive_intelligence.risk import RiskIntelligence
from applications.legal_enterprise.executive_intelligence.services import (
    ExecutiveIntelligenceDashboard,
    ExecutiveKnowledge,
)
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


class ExecutiveIntelligenceSuite:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.executive = ExecutiveLegalDashboard(self.store)
        self.analytics = LegalAnalytics(self.store)
        self.risk = RiskIntelligence(self.store)
        self.forecasting = RegulatoryForecasting(self.store)
        self.decisions = DecisionSupport(self.store)
        self.ai = AIExecutiveIntelligence(self.store)
        self.alerts = AlertCenter(self.store)
        self.knowledge = ExecutiveKnowledge(self.store)
        self.dashboard = ExecutiveIntelligenceDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        overview = self.executive.snapshot(section="overview")
        portfolio = self.executive.snapshot(section="portfolio")
        critical = self.executive.snapshot(section="critical_events")
        hearings = self.executive.snapshot(section="hearings")
        deadlines = self.executive.snapshot(section="compliance_deadlines")
        high_risk = self.executive.snapshot(section="high_risk_cases")
        contracts = self.executive.snapshot(section="pending_contracts")
        tasks = self.executive.snapshot(section="open_tasks")

        case_success = self.analytics.report(kind="case_success")
        court = self.analytics.report(kind="court_performance")
        judge = self.analytics.report(kind="judge")
        cost = self.analytics.report(kind="legal_cost")
        contract_an = self.analytics.report(kind="contract")
        compliance_an = self.analytics.report(kind="compliance")
        risk_trend = self.analytics.report(kind="risk_trend")

        enterprise = self.risk.score(
            score_type="enterprise", subject="LexCorp Holdings", value=58, detail="portfolio blended"
        )
        dept = self.risk.score(score_type="department", subject="Litigation", value=64)
        counterparty = self.risk.score(score_type="counterparty", subject="Acme Ops", value=72)
        contract_risk = self.risk.score(score_type="contract", subject="MSA-44", value=61)
        lit_fc = self.risk.forecast(forecast_type="litigation", projected_score=60)
        comp_fc = self.risk.forecast(forecast_type="compliance", projected_score=52)
        reg_exp = self.risk.forecast(forecast_type="regulatory_exposure", projected_score=55)
        ctrend = self.risk.forecast(forecast_type="contract_trend", projected_score=48)

        upcoming = self.forecasting.register(
            action="upcoming_change", title="DPL amendment 2026", impact="high", industry="data"
        )
        amendment = self.forecasting.register(
            action="amendment", title="Civil Code Art. 10 revision monitoring"
        )
        industry = self.forecasting.register(
            action="industry_impact", title="Financial services licensing impact", industry="finance"
        )
        corp_fc = self.forecasting.register(
            action="compliance_forecast", title="Q4 corporate compliance outlook"
        )
        leg_alert = self.forecasting.register(
            action="legislative_alert", title="Draft bill on AI liability", impact="high"
        )
        ai_impact = self.forecasting.register(
            action="ai_impact_report", title="AI regulatory impact on LexCorp operations"
        )

        exec_rec = self.decisions.recommend(
            kind="executive",
            title="Escalate CASE-1001 for GC review",
            priority="critical",
            items=["Assign senior counsel", "Prepare board note"],
        )
        priority = self.decisions.recommend(
            kind="priority_action", title="Clear overdue compliance items", priority="high"
        )
        strategy = self.decisions.recommend(
            kind="strategy", title="Consolidate related commercial disputes"
        )
        resources = self.decisions.recommend(
            kind="resource_allocation", title="Shift 2 FTE to regulatory response"
        )
        mitigate = self.decisions.recommend(
            kind="mitigation", title="Cap residual MSA liability via amendment"
        )
        scenario = self.decisions.recommend(
            kind="scenario",
            title="Settlement vs trial for CASE-1001",
            items=["Settle at 40%", "Proceed to hearing"],
        )

        daily = self.ai.report(report_type="daily_briefing")
        weekly = self.ai.report(report_type="weekly_summary")
        monthly = self.ai.report(report_type="monthly_risk")
        nl = self.ai.report(report_type="nl_report", focus="board pack")
        insight = self.ai.report(report_type="strategic_insight", focus="regulatory exposure")
        qa = self.ai.ask(question="What are the top legal risks this week?")

        a_crit = self.alerts.raise_alert(
            alert_type="critical", title="Injunction hearing tomorrow", severity="critical"
        )
        a_dead = self.alerts.raise_alert(
            alert_type="deadline", title="Policy attestation due 2026-07-31"
        )
        a_comp = self.alerts.raise_alert(
            alert_type="compliance", title="Two overdue checklist items"
        )
        a_court = self.alerts.raise_alert(alert_type="court", title="CASE-1001 hearing scheduled")
        a_ctr = self.alerts.raise_alert(alert_type="contract", title="MSA-44 pending GC approval")
        a_reg = self.alerts.raise_alert(
            alert_type="regulatory", title="Legislative alert: AI liability draft"
        )

        self.knowledge.publish(base="executive", key=overview["snapshot_id"], payload={"section": "overview"})
        self.knowledge.publish(base="risk", key=enterprise["risk_id"], payload={"score": enterprise["score"]})
        self.knowledge.publish(base="forecast", key=upcoming["forecast_id"], payload={"title": upcoming["title"]})
        self.knowledge.publish(
            base="recommendation", key=exec_rec["recommendation_id"], payload={"title": exec_rec["title"]}
        )
        self.knowledge.publish(base="alert", key=a_crit["alert_id"], payload={"title": a_crit["title"]})

        dash_e = self.dashboard.render(dashboard_type="executive")
        dash_r = self.dashboard.render(dashboard_type="risk")
        dash_f = self.dashboard.render(dashboard_type="forecast")
        dash_s = self.dashboard.render(dashboard_type="strategy")
        dash_o = self.dashboard.render(dashboard_type="operations")

        return {
            "bootstrap": True,
            "overview_id": overview["snapshot_id"],
            "portfolio_id": portfolio["snapshot_id"],
            "critical_id": critical["snapshot_id"],
            "hearings_id": hearings["snapshot_id"],
            "deadlines_id": deadlines["snapshot_id"],
            "high_risk_id": high_risk["snapshot_id"],
            "contracts_id": contracts["snapshot_id"],
            "tasks_id": tasks["snapshot_id"],
            "case_success_id": case_success["report_id"],
            "court_id": court["report_id"],
            "judge_id": judge["report_id"],
            "cost_id": cost["report_id"],
            "contract_analytics_id": contract_an["report_id"],
            "compliance_analytics_id": compliance_an["report_id"],
            "risk_trend_id": risk_trend["report_id"],
            "enterprise_risk_id": enterprise["risk_id"],
            "department_risk_id": dept["risk_id"],
            "counterparty_risk_id": counterparty["risk_id"],
            "contract_risk_id": contract_risk["risk_id"],
            "litigation_forecast_id": lit_fc["forecast_id"],
            "compliance_forecast_id": comp_fc["forecast_id"],
            "regulatory_exposure_id": reg_exp["forecast_id"],
            "contract_trend_id": ctrend["forecast_id"],
            "upcoming_id": upcoming["forecast_id"],
            "amendment_id": amendment["forecast_id"],
            "industry_id": industry["forecast_id"],
            "corp_forecast_id": corp_fc["forecast_id"],
            "legislative_alert_id": leg_alert["forecast_id"],
            "ai_impact_id": ai_impact["forecast_id"],
            "exec_rec_id": exec_rec["recommendation_id"],
            "priority_id": priority["recommendation_id"],
            "strategy_id": strategy["recommendation_id"],
            "resources_id": resources["recommendation_id"],
            "mitigation_id": mitigate["recommendation_id"],
            "scenario_id": scenario["recommendation_id"],
            "daily_id": daily["report_id"],
            "weekly_id": weekly["report_id"],
            "monthly_id": monthly["report_id"],
            "nl_report_id": nl["report_id"],
            "insight_id": insight["report_id"],
            "qa_id": qa["qa_id"],
            "alert_critical_id": a_crit["alert_id"],
            "alert_deadline_id": a_dead["alert_id"],
            "alert_compliance_id": a_comp["alert_id"],
            "alert_court_id": a_court["alert_id"],
            "alert_contract_id": a_ctr["alert_id"],
            "alert_regulatory_id": a_reg["alert_id"],
            "dashboard_executive_id": dash_e["dashboard_id"],
            "dashboard_risk_id": dash_r["dashboard_id"],
            "dashboard_forecast_id": dash_f["dashboard_id"],
            "dashboard_strategy_id": dash_s["dashboard_id"],
            "dashboard_operations_id": dash_o["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "executive": self.executive.status(),
            "analytics": self.analytics.status(),
            "risk": self.risk.status(),
            "forecasting": self.forecasting.status(),
            "decisions": self.decisions.status(),
            "ai": self.ai.status(),
            "alerts": self.alerts.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


executive_intelligence = ExecutiveIntelligenceSuite()
