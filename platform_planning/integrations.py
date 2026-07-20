# Integration bridges — Reasoning, Workflow, Tools, Memory, Agents, Orchestrator.

from __future__ import annotations

import logging
from typing import Any

from platform_planning.models import PlanningContext

logger = logging.getLogger(__name__)


class PlanningIntegrations:
    @staticmethod
    async def context_from_reasoning(agent_id: str, goal: str, *, user_id: str | None = None) -> PlanningContext:
        reasoning_result: dict[str, Any] = {}
        intent: str | None = None
        capabilities: list[str] = []
        tools: list[str] = []
        memory: dict[str, Any] = {}

        try:
            from platform_reasoning import reasoning_engine
            from platform_reasoning.integrations import reasoning_integrations

            ctx = reasoning_integrations.context_from_agent(agent_id, goal, user_id=user_id)
            ctx = reasoning_integrations.enrich_with_memory(ctx, user_id=user_id)
            result = await reasoning_engine.reason(ctx)
            reasoning_result = result.to_dict()
            intent = result.intent
            capabilities = list(ctx.capabilities)
            tools = list(ctx.available_tools)
            memory = dict(ctx.memory_context)
        except Exception:
            logger.debug("reasoning_engine unavailable for planning context")

        if not capabilities:
            try:
                from platform_agents.registry import agent_registry
                agent = agent_registry.get(agent_id)
                capabilities = list(agent.metadata().capabilities)
            except Exception:
                pass

        return PlanningContext(
            goal=goal,
            agent_id=agent_id,
            user_id=user_id,
            intent=intent,
            capabilities=capabilities,
            available_tools=tools,
            available_agents=[agent_id] if agent_id else [],
            memory_context=memory,
            reasoning_result=reasoning_result,
            permissions=["execute"],
        )

    @staticmethod
    async def execute_plan_workflow(result_dict: dict[str, Any]) -> dict[str, Any]:
        """Convert planning result to workflow execution."""
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            wf_def = result_dict.get("workflow_definition", {})
            steps = wf_def.get("workflow_steps", [])
            if not steps:
                return {"executed": False, "reason": "no workflow steps"}

            workflow = await workflow_engine.create_workflow(
                wf_def.get("name", "Generated Plan"),
                steps,
            )
            executed = await workflow_engine.execute_workflow(workflow.workflow_id)
            return {"executed": True, "workflow_id": workflow.workflow_id, "status": executed.status.value}
        except Exception as exc:
            logger.debug("workflow execution unavailable: %s", exc)
            return {"executed": False, "reason": str(exc)}

    @staticmethod
    def orchestrator_routing(plan_dict: dict[str, Any]) -> dict[str, Any]:
        steps = plan_dict.get("steps", [])
        first_cap = next((s.get("capability") for s in steps if s.get("capability")), None)
        return {
            "plan_id": plan_dict.get("plan_id"),
            "first_capability": first_cap,
            "step_count": len(steps),
            "estimated_cost": plan_dict.get("estimated_cost", 0),
        }


planning_integrations = PlanningIntegrations()
