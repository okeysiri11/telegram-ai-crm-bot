"""AI Agent Suite facade — Sprint 19.3."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.ai_agents.automation import AutonomousAutomation
from applications.enterprise_hub.ai_agents.collaboration import MultiAgentCollaboration
from applications.enterprise_hub.ai_agents.execution import AgentExecution
from applications.enterprise_hub.ai_agents.governance import AgentGovernance
from applications.enterprise_hub.ai_agents.intelligence import AgentIntelligence
from applications.enterprise_hub.ai_agents.registry import AgentRegistry
from applications.enterprise_hub.ai_agents.services import AgentDashboard, AgentMetaKnowledge
from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class AIAgentSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = AgentRegistry(self.store)
        self.execution = AgentExecution(self.store)
        self.collaboration = MultiAgentCollaboration(self.store)
        self.automation = AutonomousAutomation(self.store)
        self.intelligence = AgentIntelligence(self.store)
        self.governance = AgentGovernance(self.store)
        self.meta = AgentMetaKnowledge(self.store)
        self.dashboard = AgentDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        auto_agent = self.registry.register_agent(
            name="Automotive Ops Agent",
            agent_type="automotive",
            capabilities=["fleet_ops", "vin_lookup"],
            permissions=["read_vehicles", "dispatch"],
        )
        agro_agent = self.registry.register_agent(
            name="Agro Field Agent",
            agent_type="agro",
            capabilities=["yield_forecast"],
            permissions=["read_fields"],
        )
        port_agent = self.registry.register_agent(
            name="Port Logistics Agent",
            agent_type="port",
            capabilities=["berth_planning"],
            permissions=["read_berths"],
        )
        crypto_agent = self.registry.register_agent(
            name="Crypto Treasury Agent",
            agent_type="crypto",
            capabilities=["wallet_monitor"],
            permissions=["read_wallets"],
        )
        legal_agent = self.registry.register_agent(
            name="Legal Case Agent",
            agent_type="legal",
            capabilities=["case_intake"],
            permissions=["read_cases"],
        )
        finance_agent = self.registry.register_agent(
            name="Finance CFO Agent",
            agent_type="finance",
            capabilities=["cash_forecast", "settlement"],
            permissions=["approve_journals", "view_treasury"],
        )
        general = self.registry.register_agent(
            name="Enterprise General Agent",
            agent_type="general",
            capabilities=["coordination", "routing"],
            permissions=["hub_coordinate"],
            profile={"role": "coordinator"},
        )

        cap = self.registry.register_capability(name="cross_platform_sync", description="Sync across verticals")
        perm = self.registry.register_permission(name="hub_coordinate", scope="enterprise")
        life = self.registry.set_lifecycle(agent_id=general["agent_id"], lifecycle="active")
        for agent in (
            auto_agent,
            agro_agent,
            port_agent,
            crypto_agent,
            legal_agent,
            finance_agent,
        ):
            self.registry.set_lifecycle(agent_id=agent["agent_id"], lifecycle="active")
        ver = self.registry.version_agent(agent_id=general["agent_id"], note="bootstrap v2")

        task_seq = self.execution.assign_task(
            agent_id=finance_agent["agent_id"],
            title="Reconcile daily cash",
            priority=1,
            mode="sequential",
        )
        task_par = self.execution.assign_task(
            agent_id=general["agent_id"],
            title="Fan-out health checks",
            priority=2,
            mode="parallel",
        )
        prio = self.execution.prioritize(task_id=task_seq["task_id"], priority=0)
        exec1 = self.execution.execute(task_id=task_seq["task_id"])
        exec2 = self.execution.execute(task_id=task_par["task_id"])
        retry = self.execution.retry(task_id=task_par["task_id"], reason="transient timeout")
        hist = self.execution.record_history(task_id=task_seq["task_id"], detail="completed cash reconcile")

        msg = self.collaboration.communicate(
            from_agent_id=general["agent_id"],
            to_agent_id=finance_agent["agent_id"],
            message="Prepare Q2 liquidity brief",
        )
        ctx = self.collaboration.share_context(
            agent_ids=[general["agent_id"], finance_agent["agent_id"], legal_agent["agent_id"]],
            label="board_prep",
            payload={"quarter": "Q2"},
        )
        dele = self.collaboration.delegate(
            from_agent_id=general["agent_id"],
            to_agent_id=port_agent["agent_id"],
            task_ref=task_par["task_id"],
        )
        cons = self.collaboration.consensus(
            agent_ids=[general["agent_id"], finance_agent["agent_id"]],
            topic="cash_pool",
            outcome="approved",
        )
        conf = self.collaboration.resolve_conflict(
            detail="priority clash on berth vs treasury window",
            resolution="finance_first",
        )
        plan = self.collaboration.plan(
            agent_ids=[general["agent_id"], auto_agent["agent_id"], agro_agent["agent_id"]],
            objective="Cross-vertical weekend ops",
            steps=["collect", "correlate", "report"],
        )

        auto_sched = self.automation.create(
            name="Nightly settlement",
            kind="scheduled",
            agent_id=finance_agent["agent_id"],
            schedule="0 2 * * *",
        )
        auto_evt = self.automation.create(
            name="Invoice paid trigger",
            kind="event_driven",
            agent_id=finance_agent["agent_id"],
            event="invoice.paid",
        )
        auto_rule = self.automation.create(
            name="Margin guardrail",
            kind="rule_based",
            agent_id=general["agent_id"],
            rule="margin < 0.3 => alert",
        )
        auto_appr = self.automation.create(
            name="Large transfer gate",
            kind="approval",
            agent_id=finance_agent["agent_id"],
        )
        appr = self.automation.request_approval(
            automation_id=auto_appr["automation_id"], requester="cfo"
        )
        hitl = self.automation.human_in_loop(
            automation_id=auto_appr["automation_id"],
            operator="cfo@bidex.io",
            decision="approve",
        )
        estop = self.automation.emergency_stop(
            automation_id=auto_rule["automation_id"], reason="false positive spike"
        )

        intel_task = self.intelligence.insight(
            insight_type="task_optimization", subject="cash reconcile", detail="batch invoices"
        )
        intel_res = self.intelligence.insight(
            insight_type="resource_optimization", subject="agent pool", detail="scale finance"
        )
        intel_rec = self.intelligence.insight(
            insight_type="performance_recommendation", subject="latency", detail="cache VIN"
        )
        intel_reuse = self.intelligence.insight(
            insight_type="knowledge_reuse", subject="settlement template", detail="reuse orch plan"
        )
        intel_ctx = self.intelligence.insight(
            insight_type="context_decision", subject="port+finance", detail="align cutoffs"
        )
        fb = self.intelligence.feedback(
            agent_id=finance_agent["agent_id"], outcome="reconcile_ok", score=0.98
        )

        health = self.governance.health_check(agent_id=general["agent_id"])
        metrics = self.governance.metrics(
            agent_id=finance_agent["agent_id"], latency_ms=42.0, success_rate=0.99
        )
        audit = self.governance.audit(action="bootstrap", actor="system", detail="Sprint 19.3 seed")
        sec = self.governance.security_event(
            agent_id=crypto_agent["agent_id"], severity="info", detail="wallet scan ok"
        )
        pval = self.governance.validate_permission(
            agent_id=finance_agent["agent_id"], permission="view_treasury"
        )
        res = self.governance.track_resources(
            agent_id=general["agent_id"], cpu=0.12, memory_mb=256.0
        )

        self.meta.publish(base="agent_graph", key=general["agent_id"], payload={"role": "coordinator"})
        self.meta.publish(base="capability", key=cap["capability_id"], payload={"name": cap["name"]})
        self.meta.publish(base="execution", key=exec1["execution_id"], payload={"task": task_seq["title"]})
        self.meta.publish(base="automation", key=auto_sched["automation_id"], payload={"kind": "scheduled"})
        self.meta.publish(base="performance", key=metrics["metric_id"], payload={"success_rate": 0.99})

        dash_a = self.dashboard.render(dashboard_type="agents")
        dash_auto = self.dashboard.render(dashboard_type="automation")
        dash_ex = self.dashboard.render(dashboard_type="execution")
        dash_perf = self.dashboard.render(dashboard_type="performance")
        dash_gov = self.dashboard.render(dashboard_type="governance")

        return {
            "bootstrap": True,
            "agent_automotive_id": auto_agent["agent_id"],
            "agent_agro_id": agro_agent["agent_id"],
            "agent_port_id": port_agent["agent_id"],
            "agent_crypto_id": crypto_agent["agent_id"],
            "agent_legal_id": legal_agent["agent_id"],
            "agent_finance_id": finance_agent["agent_id"],
            "agent_general_id": general["agent_id"],
            "capability_id": cap["capability_id"],
            "permission_id": perm["permission_id"],
            "lifecycle_id": life["agent_id"],
            "version_id": ver["version_id"],
            "task_sequential_id": task_seq["task_id"],
            "task_parallel_id": task_par["task_id"],
            "prioritize_id": prio["task_id"],
            "execution_sequential_id": exec1["execution_id"],
            "execution_parallel_id": exec2["execution_id"],
            "retry_id": retry["retry_id"],
            "history_id": hist["history_id"],
            "message_id": msg["message_id"],
            "shared_context_id": ctx["context_id"],
            "delegation_id": dele["delegation_id"],
            "consensus_id": cons["consensus_id"],
            "conflict_id": conf["conflict_id"],
            "plan_id": plan["plan_id"],
            "automation_scheduled_id": auto_sched["automation_id"],
            "automation_event_id": auto_evt["automation_id"],
            "automation_rule_id": auto_rule["automation_id"],
            "automation_approval_id": auto_appr["automation_id"],
            "approval_id": appr["approval_id"],
            "hitl_id": hitl["hitl_id"],
            "emergency_stop_id": estop["stop_id"],
            "intel_task_id": intel_task["insight_id"],
            "intel_resource_id": intel_res["insight_id"],
            "intel_recommendation_id": intel_rec["insight_id"],
            "intel_reuse_id": intel_reuse["insight_id"],
            "intel_context_id": intel_ctx["insight_id"],
            "feedback_id": fb["feedback_id"],
            "health_id": health["health_id"],
            "metric_id": metrics["metric_id"],
            "audit_id": audit["audit_id"],
            "security_id": sec["security_id"],
            "permission_check_id": pval["check_id"],
            "resource_id": res["resource_id"],
            "dashboard_agents_id": dash_a["dashboard_id"],
            "dashboard_automation_id": dash_auto["dashboard_id"],
            "dashboard_execution_id": dash_ex["dashboard_id"],
            "dashboard_performance_id": dash_perf["dashboard_id"],
            "dashboard_governance_id": dash_gov["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "execution": self.execution.status(),
            "collaboration": self.collaboration.status(),
            "automation": self.automation.status(),
            "intelligence": self.intelligence.status(),
            "governance": self.governance.status(),
            "meta": self.meta.status(),
            "dashboard": self.dashboard.status(),
        }


ai_agents = AIAgentSuite()
