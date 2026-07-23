"""AI Orchestration Suite facade — Sprint 20.1."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.ai_orchestrator.agents.capabilities import AgentCapabilities
from applications.enterprise_hub.ai_orchestrator.agents.health import AgentHealth
from applications.enterprise_hub.ai_orchestrator.agents.lifecycle import AgentLifecycle
from applications.enterprise_hub.ai_orchestrator.agents.registry import AgentRegistry
from applications.enterprise_hub.ai_orchestrator.analytics.costs import CostAnalytics
from applications.enterprise_hub.ai_orchestrator.analytics.optimization import OptimizationEngine
from applications.enterprise_hub.ai_orchestrator.analytics.performance import PerformanceAnalytics
from applications.enterprise_hub.ai_orchestrator.context_manager import ContextManager
from applications.enterprise_hub.ai_orchestrator.dispatcher import Dispatcher
from applications.enterprise_hub.ai_orchestrator.execution_engine import ExecutionEngine
from applications.enterprise_hub.ai_orchestrator.memory_router import MemoryRouter
from applications.enterprise_hub.ai_orchestrator.orchestrator import AIOrchestrator
from applications.enterprise_hub.ai_orchestrator.planner import Planner
from applications.enterprise_hub.ai_orchestrator.policy_engine import PolicyEngine
from applications.enterprise_hub.ai_orchestrator.result_aggregator import ResultAggregator
from applications.enterprise_hub.ai_orchestrator.scheduler import Scheduler
from applications.enterprise_hub.ai_orchestrator.strategies.collaborative import CollaborativeStrategy
from applications.enterprise_hub.ai_orchestrator.strategies.delegation import DelegationStrategy
from applications.enterprise_hub.ai_orchestrator.strategies.parallel import ParallelStrategy
from applications.enterprise_hub.ai_orchestrator.strategies.sequential import SequentialStrategy
from applications.enterprise_hub.ai_orchestrator.strategies.voting import VotingStrategy
from applications.enterprise_hub.ai_orchestrator.task_manager import TaskManager
from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class AIOrchestrationSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = AgentRegistry(self.store)
        self.lifecycle = AgentLifecycle(self.store)
        self.health = AgentHealth(self.store)
        self.capabilities = AgentCapabilities(self.store)
        self.tasks = TaskManager(self.store)
        self.planner = Planner(self.store)
        self.dispatcher = Dispatcher(self.store)
        self.scheduler = Scheduler(self.store)
        self.execution = ExecutionEngine(self.store)
        self.context = ContextManager(self.store)
        self.memory = MemoryRouter(self.store)
        self.aggregator = ResultAggregator(self.store)
        self.policy = PolicyEngine(self.store)
        self.orchestrator = AIOrchestrator(self.store)
        self.performance = PerformanceAnalytics(self.store)
        self.costs = CostAnalytics(self.store)
        self.optimization = OptimizationEngine(self.store)
        self.strategies = {
            "sequential": SequentialStrategy(),
            "parallel": ParallelStrategy(),
            "voting": VotingStrategy(),
            "delegation": DelegationStrategy(),
            "collaborative": CollaborativeStrategy(),
        }

    def bootstrap(self) -> dict[str, Any]:
        legal = self.registry.register(
            name="Legal Agent",
            specialization="legal",
            tasks=["legal", "compliance"],
            model="gpt-legal",
            cost_per_task=0.04,
        )
        finance = self.registry.register(
            name="Finance Agent",
            specialization="finance",
            tasks=["finance", "pricing"],
            model="gpt-finance",
            cost_per_task=0.05,
        )
        crm = self.registry.register(
            name="CRM Agent",
            specialization="crm",
            tasks=["crm", "accounts"],
            model="gpt-crm",
            cost_per_task=0.03,
        )
        writer = self.registry.register(
            name="AI Writer",
            specialization="writer",
            tasks=["writer", "draft"],
            model="gpt-writer",
            cost_per_task=0.02,
        )
        aggregator = self.registry.register(
            name="Final Aggregator",
            specialization="aggregator",
            tasks=["aggregator", "merge"],
            model="gpt-merge",
            cost_per_task=0.01,
        )
        backup_legal = self.registry.register(
            name="Legal Backup",
            specialization="legal",
            tasks=["legal"],
            model="gpt-legal-lite",
            cost_per_task=0.02,
        )

        for agent in (legal, finance, crm, writer, aggregator, backup_legal):
            self.lifecycle.start(agent_id=agent["agent_id"])
            self.health.check(agent_id=agent["agent_id"])
            self.capabilities.describe(agent_id=agent["agent_id"])

        pol_collab = self.policy.define(
            kind="collaboration",
            name="default-collab",
            rules={"strategies": ["sequential", "parallel", "collaborative", "voting", "delegation"]},
        )
        pol_cost = self.policy.define(
            kind="cost_quality",
            name="cost-cap",
            rules={"max_cost": 100.0},
        )
        pol_prio = self.policy.define(
            kind="priority",
            name="critical-first",
            rules={"order": ["critical", "high", "normal", "low"]},
        )
        pol_limit = self.policy.define(
            kind="model_limit",
            name="model-budget",
            rules={"max_tokens": 128000},
        )

        run = self.orchestrator.orchestrate(
            request="Подготовить коммерческое предложение.",
            strategy="sequential",
            priority="high",
        )
        parallel = self.orchestrator.orchestrate(
            request="Собрать обзор рынка параллельно.",
            strategy="parallel",
            priority="normal",
        )

        perf = self.performance.report()
        cost = self.costs.report()
        opt = self.optimization.recommend()

        return {
            "bootstrap": True,
            "agent_legal_id": legal["agent_id"],
            "agent_finance_id": finance["agent_id"],
            "agent_crm_id": crm["agent_id"],
            "agent_writer_id": writer["agent_id"],
            "agent_aggregator_id": aggregator["agent_id"],
            "agent_backup_legal_id": backup_legal["agent_id"],
            "policy_collaboration_id": pol_collab["policy_id"],
            "policy_cost_id": pol_cost["policy_id"],
            "policy_priority_id": pol_prio["policy_id"],
            "policy_model_limit_id": pol_limit["policy_id"],
            "task_id": run["task_id"],
            "plan_id": run["plan_id"],
            "dispatch_id": run["dispatch_id"],
            "execution_id": run["execution_id"],
            "aggregation_id": run["aggregation_id"],
            "context_id": run["context_id"],
            "parallel_task_id": parallel["task_id"],
            "performance_id": perf["analytics_id"],
            "cost_id": cost["analytics_id"],
            "optimization_id": opt["analytics_id"],
            "strategies": {k: v.describe() for k, v in self.strategies.items()},
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "tasks": self.tasks.status(),
            "scheduler": self.scheduler.status(),
            "execution": self.execution.status(),
            "memory": self.memory.status(),
            "policy": self.policy.status(),
        }


ai_orchestrator = AIOrchestrationSuite()
