# Integration bridges — Workflow, AI engines, Tools, Observability, Security, Agents, Orchestrator.

from __future__ import annotations

import logging
from typing import Any

from platform_reliability.models import Checkpoint, RecoveryContext, RecoveryPolicy

logger = logging.getLogger(__name__)


class ReliabilityIntegrations:
    @staticmethod
    async def checkpoint_from_workflow(workflow_id: str, snapshot: dict[str, Any]) -> Checkpoint:
        from platform_reliability.checkpoint_manager import checkpoint_manager

        return checkpoint_manager.save(workflow_id=workflow_id, snapshot=snapshot)

    @staticmethod
    async def restore_planning_state(plan_id: str) -> dict[str, Any]:
        try:
            from platform_planning import planning_engine

            plan = planning_engine.get_plan(plan_id)
            return plan.to_dict()
        except Exception:
            logger.debug("planning_engine unavailable for recovery")
            return {}

    @staticmethod
    async def restore_decision_state(decision_id: str) -> dict[str, Any]:
        try:
            from platform_decision import decision_engine

            trace = decision_engine.get_trace(decision_id)
            return trace.to_dict() if trace else {}
        except Exception:
            logger.debug("decision_engine unavailable for recovery")
            return {}

    @staticmethod
    async def record_learning_from_failure(ctx: RecoveryContext, result_dict: dict[str, Any]) -> None:
        try:
            from platform_learning.feedback_collector import feedback_collector

            feedback_collector.collect_error_report(
                ctx.error or "recovery failure",
                agent_id=ctx.agent_id,
                severity=70.0,
            )
        except Exception:
            logger.debug("learning_engine unavailable")

    @staticmethod
    async def observability_log_recovery(ctx: RecoveryContext, result_dict: dict[str, Any]) -> None:
        try:
            from platform_observability import observability_manager

            observability_manager._logs.info(
                f"Recovery {result_dict.get('action')}: {result_dict.get('message')}",
                component="reliability",
                extra=ctx.to_dict(),
            )
        except Exception:
            logger.debug("observability unavailable")

    @staticmethod
    def orchestrator_failover(agent_id: str) -> list[str]:
        try:
            from platform_agents.registry import agent_registry

            return [m.id for m in agent_registry.list_agents() if m.id != agent_id][:3]
        except Exception:
            return []

    @staticmethod
    async def secure_recovery(principal_id: str | None = None) -> bool:
        try:
            from platform_security.models import SecurityPrincipal
            from platform_security.security_manager import security_manager

            if not principal_id:
                return True
            principal = SecurityPrincipal(principal_id=principal_id, roles=["operator"])
            return await security_manager.authorize(principal, "workflow.execute")
        except Exception:
            return True


reliability_integrations = ReliabilityIntegrations()
