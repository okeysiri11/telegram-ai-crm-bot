"""Orchestrator Suite facade — Sprint 19.1."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.orchestrator.core import OrchestratorCore
from applications.enterprise_hub.orchestrator.decisions import AIDecisionEngine
from applications.enterprise_hub.orchestrator.explainability import AIExplainability
from applications.enterprise_hub.orchestrator.intent import IntentUnderstanding
from applications.enterprise_hub.orchestrator.monitoring import OrchestratorMonitoring
from applications.enterprise_hub.orchestrator.routing import CrossPlatformRouting
from applications.enterprise_hub.orchestrator.services import (
    OrchestratorDashboard,
    OrchestratorKnowledge,
)
from applications.enterprise_hub.orchestrator.workflow_intel import WorkflowIntelligence
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class OrchestratorSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.core = OrchestratorCore(self.store)
        self.intent = IntentUnderstanding(self.store)
        self.workflow_intel = WorkflowIntelligence(self.store)
        self.routing = CrossPlatformRouting(self.store)
        self.decisions = AIDecisionEngine(self.store)
        self.monitoring = OrchestratorMonitoring(self.store)
        self.explainability = AIExplainability(self.store)
        self.knowledge = OrchestratorKnowledge(self.store)
        self.dashboard = OrchestratorDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        wf_seq = self.core.register_workflow(
            name="Invoice Settlement",
            kind="sequential",
            steps=["validate", "route:finance", "post_ledger", "notify"],
        )
        wf_par = self.core.register_workflow(
            name="Multi-Platform Sync",
            kind="parallel",
            steps=["route:finance", "route:legal", "route:crypto"],
        )
        wf_cond = self.core.register_workflow(
            name="Conditional Approval",
            kind="conditional",
            steps=["assess", "if_high_risk", "approve", "execute"],
        )
        plan = self.core.plan(workflow_id=wf_seq["workflow_id"], context={"amount": 10000})
        queue = self.core.enqueue(plan_id=plan["plan_id"], priority=2)
        deps = self.core.resolve_dependencies(
            workflow_id=wf_par["workflow_id"], depends_on=[wf_seq["workflow_id"]]
        )
        exe = self.core.execute(workflow_id=wf_seq["workflow_id"], plan_id=plan["plan_id"])
        sch = self.core.schedule(workflow_id=wf_par["workflow_id"], cron="0 6 * * *")
        retry = self.core.retry(execution_id=exe["execution_id"])
        rb = self.core.rollback(execution_id=exe["execution_id"], reason="demo_rollback")

        intent = self.intent.detect(
            utterance="Settle dealer payment across finance and automotive",
            task_class="settlement",
            priority="high",
            confidence=0.91,
            entities=["dealer", "payment"],
            context="cross_platform",
        )

        tpl = self.workflow_intel.create_template(
            name="Standard Settlement", kind="sequential", steps=["intake", "route", "settle"]
        )
        dyn = self.workflow_intel.generate(
            name="Dynamic Trade Flow",
            intent="process OTC trade",
            platforms=["crypto", "finance"],
        )
        apr = self.workflow_intel.add_approval(
            workflow_ref=wf_cond["workflow_id"], approver="cfo"
        )

        rt_auto = self.routing.route(platform="automotive", action="dealer_settlement")
        rt_agro = self.routing.route(platform="agro", action="crop_sales")
        rt_port = self.routing.route(platform="port", action="shipping_invoice")
        rt_cry = self.routing.route(platform="crypto", action="otc_settlement")
        rt_leg = self.routing.route(platform="legal", action="contract_billing")
        rt_fin = self.routing.route(platform="finance", action="payment_post")
        coord = self.routing.coordinate(
            platforms=["finance", "automotive", "legal"],
            action="settlement_pack",
            label="Dealer + Legal + Finance",
        )

        d_strat = self.decisions.decide(
            decision_type="execution_strategy", subject="Invoice Settlement", selected="sequential"
        )
        d_plat = self.decisions.decide(
            decision_type="platform_selection", subject="OTC trade", selected="crypto+finance"
        )
        d_opt = self.decisions.decide(
            decision_type="resource_optimization", subject="queue_priority", selected="priority=2"
        )
        d_conf = self.decisions.decide(
            decision_type="conflict_resolution", subject="dual_ledger_write", selected="finance_primary"
        )
        d_rec = self.decisions.decide(
            decision_type="recommendation", subject="batch_settlements", score=0.88
        )
        d_val = self.decisions.decide(
            decision_type="execution_validation", subject=exe["execution_id"], score=0.95
        )

        mon = self.monitoring.track(
            execution_id=exe["execution_id"], task="post_ledger", status="completed", duration_ms=12.5
        )
        fail = self.monitoring.failure(
            execution_id=exe["execution_id"], reason="transient", analysis="retry succeeded"
        )
        hist = self.monitoring.history(
            execution_id=exe["execution_id"], summary="Settlement completed with rollback demo"
        )

        x_reason = self.explainability.explain(
            explain_type="execution_reasoning", subject=exe["execution_id"]
        )
        x_trace = self.explainability.explain(
            explain_type="decision_trace", subject=d_plat["decision_id"]
        )
        x_sum = self.explainability.explain(
            explain_type="workflow_summary", subject=wf_seq["workflow_id"]
        )
        x_conf = self.explainability.explain(
            explain_type="execution_confidence", subject=exe["execution_id"], confidence=0.93
        )
        x_nl = self.explainability.explain(
            explain_type="nl_explanation",
            subject="board",
            narrative="Orchestrator routed settlement across finance and automotive with CFO approval gate.",
        )

        self.knowledge.publish(base="workflow", key=wf_seq["workflow_id"], payload={"name": wf_seq["name"]})
        self.knowledge.publish(base="execution", key=exe["execution_id"], payload={"status": "completed"})
        self.knowledge.publish(base="task", key=mon["monitor_id"], payload={"task": "post_ledger"})
        self.knowledge.publish(base="decision", key=d_strat["decision_id"], payload={"type": "execution_strategy"})
        self.knowledge.publish(base="routing", key=coord["coordination_id"], payload={"platforms": 3})

        dash_o = self.dashboard.render(dashboard_type="orchestrator")
        dash_w = self.dashboard.render(dashboard_type="workflow")
        dash_e = self.dashboard.render(dashboard_type="execution")
        dash_p = self.dashboard.render(dashboard_type="platform_activity")
        dash_a = self.dashboard.render(dashboard_type="ai_decision")

        return {
            "bootstrap": True,
            "workflow_sequential_id": wf_seq["workflow_id"],
            "workflow_parallel_id": wf_par["workflow_id"],
            "workflow_conditional_id": wf_cond["workflow_id"],
            "plan_id": plan["plan_id"],
            "queue_id": queue["queue_id"],
            "dependency_id": deps["dependency_id"],
            "execution_id": exe["execution_id"],
            "schedule_id": sch["schedule_id"],
            "retry_id": retry["retry_id"],
            "rollback_id": rb["rollback_id"],
            "intent_id": intent["intent_id"],
            "template_id": tpl["template_id"],
            "dynamic_id": dyn["dynamic_id"],
            "approval_id": apr["approval_id"],
            "route_automotive_id": rt_auto["route_id"],
            "route_agro_id": rt_agro["route_id"],
            "route_port_id": rt_port["route_id"],
            "route_crypto_id": rt_cry["route_id"],
            "route_legal_id": rt_leg["route_id"],
            "route_finance_id": rt_fin["route_id"],
            "coordination_id": coord["coordination_id"],
            "decision_strategy_id": d_strat["decision_id"],
            "decision_platform_id": d_plat["decision_id"],
            "decision_optimize_id": d_opt["decision_id"],
            "decision_conflict_id": d_conf["decision_id"],
            "decision_recommend_id": d_rec["decision_id"],
            "decision_validate_id": d_val["decision_id"],
            "monitor_id": mon["monitor_id"],
            "failure_id": fail["failure_id"],
            "history_id": hist["history_id"],
            "explain_reasoning_id": x_reason["explanation_id"],
            "explain_trace_id": x_trace["explanation_id"],
            "explain_summary_id": x_sum["explanation_id"],
            "explain_confidence_id": x_conf["explanation_id"],
            "explain_nl_id": x_nl["explanation_id"],
            "dashboard_orchestrator_id": dash_o["dashboard_id"],
            "dashboard_workflow_id": dash_w["dashboard_id"],
            "dashboard_execution_id": dash_e["dashboard_id"],
            "dashboard_platform_id": dash_p["dashboard_id"],
            "dashboard_ai_decision_id": dash_a["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "core": self.core.status(),
            "intent": self.intent.status(),
            "workflow_intel": self.workflow_intel.status(),
            "routing": self.routing.status(),
            "decisions": self.decisions.status(),
            "monitoring": self.monitoring.status(),
            "explainability": self.explainability.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


orchestrator = OrchestratorSuite()
