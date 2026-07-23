"""Skill manager / engine — run multi-tool skill chains."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.ai_tools.audit import ToolAudit
from applications.enterprise_hub.ai_tools.skill_registry import SkillRegistry
from applications.enterprise_hub.ai_tools.tool_executor import ToolExecutor
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class SkillManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = SkillRegistry(self.store)
        self.executor = ToolExecutor(self.store)
        self.audit = ToolAudit(self.store)

    def register(self, **kwargs: Any) -> dict[str, Any]:
        return self.registry.register(**kwargs)

    def run(
        self,
        *,
        skill_id: str,
        agent_id: str = "system",
        user_id: str = "system",
        role: str = "agent",
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        skill = self.registry.get(skill_id)
        if skill.get("status") != "active":
            raise ValidationError(f"skill not active: {skill_id}")
        self.audit.log(event="skill_start", skill_id=skill_id, agent_id=agent_id)
        step_results = []
        total_cost = 0.0
        for step in skill.get("steps") or []:
            tool_id = step.get("tool_id")
            if not tool_id:
                raise ValidationError("skill step missing tool_id")
            step_params = {**(params or {}), **(step.get("params") or {})}
            result = self.executor.execute(
                tool_id=tool_id,
                params=step_params,
                agent_id=agent_id,
                user_id=user_id,
                role=role,
                confirmed=True,
                needs_network=bool(step.get("needs_network", False)),
            )
            step_results.append(result)
            total_cost += float(result.get("cost", 0) or 0)

        skill["usage_count"] = int(skill.get("usage_count", 0)) + 1
        self.store.ats_skills.save(skill_id, skill)
        self.audit.log(
            event="skill_complete",
            skill_id=skill_id,
            agent_id=agent_id,
            detail={"steps": len(step_results), "cost": total_cost},
        )
        return {
            "skill_id": skill_id,
            "name": skill["name"],
            "steps": step_results,
            "total_cost": total_cost,
            "status": "completed",
        }

    def status(self) -> dict[str, Any]:
        return self.registry.status()
