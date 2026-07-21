# Skill registry — dynamic skill loading and execution.

from __future__ import annotations

from typing import Any, Awaitable, Callable

from events.publisher import publish

from ecosystem.assistant.events import SkillExecutedEvent
from ecosystem.assistant.models import Skill, SkillType
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store

SkillHandler = Callable[..., Awaitable[dict[str, Any]]]


class SkillRegistry:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store
        self._handlers: dict[str, SkillHandler] = {}
        self._seed_builtin_skills()

    def _seed_builtin_skills(self) -> None:
        if self._store.skills.count() > 0:
            return
        builtins = [
            Skill(name="search_knowledge", skill_type=SkillType.TOOL, description="Search global knowledge", handler_key="search_knowledge", priority=10),
            Skill(name="plan_task", skill_type=SkillType.WORKFLOW, description="Decompose and plan a task", handler_key="plan_task", priority=20),
            Skill(name="route_agent", skill_type=SkillType.AGENT, description="Route to an AI agent", handler_key="route_agent", priority=30),
            Skill(
                name="auto_marketplace_search",
                skill_type=SkillType.APPLICATION,
                description="Search vehicles in Auto Marketplace",
                application_id="auto_marketplace",
                handler_key="auto_marketplace_search",
                priority=40,
            ),
        ]
        for skill in builtins:
            self._store.skills.save(skill.skill_id, skill)

    def _ensure_seeded(self) -> None:
        if self._store.skills.count() == 0:
            self._seed_builtin_skills()

    def register(
        self,
        name: str,
        *,
        skill_type: SkillType = SkillType.APPLICATION,
        description: str = "",
        application_id: str = "",
        handler_key: str = "",
        parameters_schema: dict[str, Any] | None = None,
        priority: int = 100,
        handler: SkillHandler | None = None,
    ) -> Skill:
        self._ensure_seeded()
        skill = Skill(
            name=name,
            skill_type=skill_type,
            description=description,
            application_id=application_id,
            handler_key=handler_key or name,
            parameters_schema=parameters_schema or {},
            priority=priority,
        )
        self._store.skills.save(skill.skill_id, skill)
        if handler:
            self._handlers[skill.handler_key] = handler
        return skill

    def load_handler(self, handler_key: str, handler: SkillHandler) -> None:
        self._handlers[handler_key] = handler

    def get(self, skill_id: str) -> Skill:
        self._ensure_seeded()
        skill = self._store.skills.get(skill_id)
        if skill is None:
            raise NotFoundError("Skill", skill_id)
        return skill

    def find_by_name(self, name: str) -> Skill | None:
        self._ensure_seeded()
        return next((s for s in self._store.skills.list_all() if s.name == name and s.is_enabled), None)

    def list_skills(
        self,
        *,
        skill_type: SkillType | None = None,
        application_id: str = "",
    ) -> list[Skill]:
        self._ensure_seeded()
        skills = [s for s in self._store.skills.list_all() if s.is_enabled]
        if skill_type:
            skills = [s for s in skills if s.skill_type == skill_type]
        if application_id:
            skills = [s for s in skills if s.application_id in ("", application_id)]
        return sorted(skills, key=lambda s: s.priority)

    async def execute(self, skill_id: str, user_id: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        skill = self.get(skill_id)
        if not skill.is_enabled:
            raise ValidationError(f"Skill disabled: {skill.name}")
        params = parameters or {}
        handler = self._handlers.get(skill.handler_key)
        if handler:
            result = await handler(user_id=user_id, skill=skill, parameters=params)
        else:
            result = await self._default_handler(skill, user_id, params)
        await publish(
            SkillExecutedEvent(
                skill_id=skill.skill_id,
                skill_name=skill.name,
                user_id=user_id,
                result_status=result.get("status", "ok"),
            )
        )
        return {"skill": skill.to_dict(), **result}

    async def _default_handler(self, skill: Skill, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if skill.handler_key == "search_knowledge":
            from ecosystem.assistant.knowledge_graph.service import knowledge_graph

            hits = knowledge_graph.semantic_search(parameters.get("query", ""), application_id=parameters.get("application_id", ""))
            return {"status": "ok", "hits": hits}
        if skill.handler_key == "plan_task":
            return {
                "status": "ok",
                "plan": {
                    "goal": parameters.get("goal", ""),
                    "steps": [
                        {"step": 1, "action": "understand", "detail": parameters.get("goal", "")},
                        {"step": 2, "action": "execute", "detail": "Run matching skills"},
                        {"step": 3, "action": "respond", "detail": "Summarize outcome"},
                    ],
                },
            }
        if skill.handler_key == "route_agent":
            return {"status": "ok", "agent_id": parameters.get("agent_id", "default-agent"), "routed": True}
        if skill.handler_key == "auto_marketplace_search":
            return {
                "status": "ok",
                "application_id": "auto_marketplace",
                "query": parameters.get("query", ""),
                "results_hint": "Use Auto Marketplace catalog search",
            }
        return {"status": "ok", "skill": skill.name, "parameters": parameters, "executed": True}


skill_registry = SkillRegistry()
