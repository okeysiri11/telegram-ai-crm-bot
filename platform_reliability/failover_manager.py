# FailoverManager — alternative agent, tool, workflow selection and graceful degradation.

from __future__ import annotations

import logging
from typing import Any

from platform_reliability.models import RecoveryAction, RecoveryContext, RecoveryResult

logger = logging.getLogger(__name__)


class FailoverManager:
    def __init__(self) -> None:
        self._fallbacks: dict[str, list[str]] = {}
        self._history: list[RecoveryResult] = []

    def reset(self) -> None:
        self._fallbacks.clear()
        self._history.clear()

    def register_fallback(self, primary: str, alternatives: list[str]) -> None:
        self._fallbacks[primary] = list(alternatives)

    async def failover_agent(self, ctx: RecoveryContext) -> RecoveryResult:
        agent_id = ctx.agent_id or "unknown"
        alternatives = await self._agent_alternatives(agent_id)
        target = alternatives[0] if alternatives else None
        if not target:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.GRACEFUL_DEGRADATION,
                execution_id=ctx.execution_id,
                message="No alternative agent available",
            )
        return RecoveryResult(
            success=True,
            action=RecoveryAction.FAILOVER,
            execution_id=ctx.execution_id,
            recovered=True,
            failover_target=target,
            message=f"Failover from {agent_id} to {target}",
        )

    async def failover_tool(self, ctx: RecoveryContext) -> RecoveryResult:
        tool_id = ctx.tool_id or "unknown"
        alts = self._fallbacks.get(tool_id, [])
        target = alts[0] if alts else None
        if not target:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.GRACEFUL_DEGRADATION,
                execution_id=ctx.execution_id,
                message=f"No fallback tool for {tool_id}",
            )
        return RecoveryResult(
            success=True,
            action=RecoveryAction.FAILOVER,
            execution_id=ctx.execution_id,
            recovered=True,
            failover_target=target,
            message=f"Failover tool {tool_id} -> {target}",
        )

    async def failover_workflow(self, ctx: RecoveryContext) -> RecoveryResult:
        return RecoveryResult(
            success=True,
            action=RecoveryAction.FAILOVER,
            execution_id=ctx.execution_id,
            recovered=True,
            failover_target="fallback_workflow",
            message="Executing fallback workflow path",
        )

    async def graceful_degrade(self, ctx: RecoveryContext) -> RecoveryResult:
        return RecoveryResult(
            success=True,
            action=RecoveryAction.GRACEFUL_DEGRADATION,
            execution_id=ctx.execution_id,
            recovered=True,
            message="Graceful degradation — reduced functionality",
            restored_state={"degraded": True, "original_error": ctx.error},
        )

    async def _agent_alternatives(self, agent_id: str) -> list[str]:
        if agent_id in self._fallbacks:
            return self._fallbacks[agent_id]
        try:
            from platform_agents.registry import agent_registry

            all_agents = [m.id for m in agent_registry.list_agents()]
            return [a for a in all_agents if a != agent_id][:3]
        except Exception:
            logger.debug("agent_registry unavailable for failover")
            return []


failover_manager = FailoverManager()
