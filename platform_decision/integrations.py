# Integration bridges — Reasoning, Planning, Workflow, Memory, Tools, Agents, Orchestrator.

from __future__ import annotations

import logging
import uuid
from typing import Any

from platform_decision.models import DecisionCandidate, DecisionContext, DecisionCriteria

logger = logging.getLogger(__name__)


class DecisionIntegrations:
    @staticmethod
    async def context_from_reasoning(
        agent_id: str,
        request: str,
        *,
        user_id: str | None = None,
    ) -> DecisionContext:
        reasoning_result: dict[str, Any] = {}
        memory: dict[str, Any] = {}
        tools: list[str] = []
        agents: list[str] = [agent_id] if agent_id else []

        try:
            from platform_reasoning import reasoning_engine
            from platform_reasoning.integrations import reasoning_integrations

            ctx = reasoning_integrations.context_from_agent(agent_id, request, user_id=user_id)
            ctx = reasoning_integrations.enrich_with_memory(ctx, user_id=user_id)
            result = await reasoning_engine.reason(ctx)
            reasoning_result = result.to_dict()
            tools = list(ctx.available_tools)
            memory = dict(ctx.memory_context)
        except Exception:
            logger.debug("reasoning_engine unavailable for decision context")

        if not agents:
            try:
                from platform_agents.registry import agent_registry

                agent = agent_registry.get(agent_id)
                agents = [agent_id]
                _ = agent.metadata()
            except Exception:
                pass

        return DecisionContext(
            request=request,
            agent_id=agent_id,
            user_id=user_id,
            reasoning_result=reasoning_result,
            memory_context=memory,
            available_tools=tools,
            available_agents=agents,
        )

    @staticmethod
    async def context_from_planning(
        agent_id: str,
        request: str,
        *,
        user_id: str | None = None,
    ) -> DecisionContext:
        ctx = await DecisionIntegrations.context_from_reasoning(agent_id, request, user_id=user_id)
        planning_result: dict[str, Any] = {}
        candidates: list[DecisionCandidate] = []

        try:
            from platform_planning import planning_engine

            plan_result = await planning_engine.plan_for_agent(agent_id, request, user_id=user_id)
            planning_result = plan_result.to_dict()
            for i, step in enumerate(plan_result.plan.steps[:5]):
                duration_ms = float(step.metadata.get("estimated_duration_ms", 1000 + i * 500))
                candidates.append(
                    DecisionCandidate(
                        candidate_id=f"plan_step_{step.step_id}",
                        name=step.name,
                        capability=step.capability,
                        agent_id=step.agent_id or agent_id,
                        plan_id=plan_result.plan.plan_id,
                        criteria=DecisionCriteria(
                            execution_cost=step.estimated_cost,
                            estimated_duration_ms=duration_ms,
                            confidence_score=70.0 - i * 5,
                            business_priority=ctx.business_priority,
                        ),
                    )
                )
        except Exception:
            logger.debug("planning_engine unavailable for decision context")

        ctx.planning_result = planning_result
        ctx.candidates = candidates
        return ctx

    @staticmethod
    def candidates_from_capabilities(
        capabilities: list[str],
        *,
        agent_id: str | None = None,
        base_cost: float = 10.0,
    ) -> list[DecisionCandidate]:
        out: list[DecisionCandidate] = []
        for i, cap in enumerate(capabilities):
            out.append(
                DecisionCandidate(
                    candidate_id=str(uuid.uuid4()),
                    name=f"Execute {cap}",
                    capability=cap,
                    agent_id=agent_id,
                    criteria=DecisionCriteria(
                        execution_cost=base_cost + i * 5,
                        estimated_duration_ms=1000 + i * 500,
                        risk_level=10.0 + i * 5,
                        confidence_score=80.0 - i * 10,
                        tool_availability=90.0,
                        agent_availability=85.0,
                        business_priority=50.0,
                    ),
                )
            )
        return out

    @staticmethod
    async def execute_selected_workflow(result_dict: dict[str, Any]) -> dict[str, Any]:
        selected = result_dict.get("selected", {})
        plan_id = selected.get("plan_id")
        if not plan_id:
            return {"executed": False, "reason": "no plan_id on selected candidate"}

        try:
            from platform_planning import planning_engine

            plan = planning_engine.get_plan(plan_id)
            from platform_planning.models import PlanningResult

            pr = PlanningResult(plan=plan, success=True)
            return await planning_engine.execute_plan(pr)
        except Exception as exc:
            logger.debug("workflow execution unavailable: %s", exc)
            return {"executed": False, "reason": str(exc)}

    @staticmethod
    def orchestrator_routing(result_dict: dict[str, Any]) -> dict[str, Any]:
        selected = result_dict.get("selected", {})
        return {
            "decision_id": result_dict.get("decision_id"),
            "capability": selected.get("capability"),
            "agent_id": selected.get("agent_id"),
            "confidence": result_dict.get("confidence", 0),
        }

    @staticmethod
    def enrich_tool_availability(context: DecisionContext) -> DecisionContext:
        try:
            from platform_tools.registry import tool_registry

            available = {t.tool_id for t in tool_registry.list_tools()}
            for c in context.candidates:
                needed = c.metadata.get("required_tools", [])
                if needed:
                    score = sum(1 for t in needed if t in available) / len(needed) * 100
                    c.criteria.tool_availability = score
                elif context.available_tools:
                    c.criteria.tool_availability = 80.0
        except Exception:
            logger.debug("tool_registry unavailable")
        return context

    @staticmethod
    def enrich_agent_availability(context: DecisionContext) -> DecisionContext:
        try:
            from platform_agents.registry import agent_registry

            for c in context.candidates:
                if c.agent_id:
                    try:
                        agent = agent_registry.get(c.agent_id)
                        meta = agent.metadata()
                        c.criteria.agent_availability = 100.0 if meta.enabled else 20.0
                    except Exception:
                        if context.available_agents and c.agent_id in context.available_agents:
                            c.criteria.agent_availability = 80.0
                        else:
                            c.criteria.agent_availability = 50.0
        except Exception:
            logger.debug("agent_registry unavailable")
        return context

    @staticmethod
    def enrich_memory_preferences(context: DecisionContext) -> DecisionContext:
        prefs = context.memory_context.get("user_preferences", {})
        if prefs:
            context.user_preferences = dict(prefs)
            for c in context.candidates:
                cap = c.capability or ""
                c.criteria.user_preference = float(prefs.get(cap, prefs.get("default", 50.0)))
        return context


decision_integrations = DecisionIntegrations()
