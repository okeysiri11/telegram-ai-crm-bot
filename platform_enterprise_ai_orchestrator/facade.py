"""Enterprise AI Orchestrator library facade — Sprint 24.0 / v7.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_ai_orchestrator.conflict import ConflictResolution
from platform_enterprise_ai_orchestrator.council import MultiAgentCouncil
from platform_enterprise_ai_orchestrator.decision import DecisionEngine
from platform_enterprise_ai_orchestrator.integrations import OrchestratorIntegrations
from platform_enterprise_ai_orchestrator.learning import AILearning
from platform_enterprise_ai_orchestrator.memory import AIMemory
from platform_enterprise_ai_orchestrator.models import PRINCIPLES
from platform_enterprise_ai_orchestrator.orchestrator import AIOrchestrator
from platform_enterprise_ai_orchestrator.owner_center import OwnerDecisionCenter
from platform_enterprise_ai_orchestrator.registry import AIRegistry


class EnterpriseAIOrchestratorLibrary:
    def __init__(self) -> None:
        self.registry = AIRegistry()
        self.council = MultiAgentCouncil()
        self.orchestrator = AIOrchestrator()
        self.decision = DecisionEngine()
        self.conflict = ConflictResolution()
        self.memory = AIMemory()
        self.learning = AILearning()
        self.owner_center = OwnerDecisionCenter()
        self.integrations = OrchestratorIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        agents = self.registry.seed_council()
        # demonstrate extensibility
        extra = self.registry.add_agent(agent_id="ai_custom_ops", role="operations", competencies=["ops", "pilots"])
        problem = "Prioritize pilot salon rollout features for v7"
        selected = self.orchestrator.select_agents(registry_agents=self.registry.list_agents(status="active"))
        deliberation = self.council.deliberate(
            problem=problem,
            agents=selected,
            context={"risk_level": "high", "growth_bias": True},
        )
        orch = self.orchestrator.run(problem=problem, agents=selected, council_result=deliberation)
        conflicts = self.conflict.resolve(
            contradictions=orch["contradictions"],
            opinions=deliberation["opinions"],
        )
        decision = self.decision.compose(
            problem=problem,
            analysis="multi_agent_council_v7",
            opinions=deliberation["opinions"],
            contradictions=orch["contradictions"],
            risks=["pilot_churn", "over_automation"],
            benefits=["unified_governance", "single_owner_brief"],
            forecast="successful_pilot_with_controls",
            action_plan=["owner_review", "approve_or_adjust", "execute_via_ops"],
        )
        for a in selected[:3]:
            self.memory.remember(
                agent_id=a["agent_id"],
                consultation=problem,
                decision_id="boot_decision",
                lesson="owner_must_approve",
            )
        learned = self.learning.learn_from_release(
            forecast="successful_pilot_with_controls",
            actual="successful_pilot_with_controls",
            confirmed=True,
        )
        owner = self.owner_center.decide(
            action="approve",
            actor="platform_owner",
            decision_id="boot_decision",
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "platform_version": "7.0.0",
            "enterprise_ai_orchestrator_ready": True,
            "multi_agent_council_ready": True,
            "council_decision_ready": True,
            "owner_decision_center_ready": True,
            "agents_registered": len(self.registry.list_agents()),
            "council_size": len(agents),
            "extensible_agent_added": extra["agent_id"],
            "has_conflicts": conflicts["has_conflict"],
            "explained_decision": decision["explained"],
            "single_consolidated_brief": True,
            "ai_may_act": False,
            "requires_owner_approval": True,
            "learned_from_confirmed": learned["learned"],
            "owner_approved": owner["approved"],
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "agents": self.registry.list_agents(),
                "deliberation": deliberation,
                "orchestration": orch,
                "conflicts": conflicts,
                "decision": decision,
                "learning": learned,
                "owner": owner,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "registry",
                "council",
                "orchestrator",
                "decision",
                "conflict",
                "memory",
                "learning",
                "owner_center",
            ],
            "principles": self.principles(),
            "agents": len(self.registry.list_agents()),
            "platform_version": "7.0.0",
        }


enterprise_ai_orchestrator_library = EnterpriseAIOrchestratorLibrary()
