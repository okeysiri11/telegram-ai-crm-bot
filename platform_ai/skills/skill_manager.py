# Skill manager — lifecycle: register, load, validate, execute, disable, reload, health.

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Type

from platform_ai.skills.exceptions import SkillNotFoundError, SkillValidationError
from platform_ai.skills.models import SkillExecutionRequest, SkillExecutionResult, SkillHealthResult, SkillRecord, SkillState
from platform_ai.skills.skill_base import AISkill
from platform_ai.skills.skill_cache import skill_cache
from platform_ai.skills.skill_context import SkillContext
from platform_ai.skills.skill_events import SkillDisabledEvent, SkillLoadedEvent, publish_skill_event
from platform_ai.skills.skill_executor import skill_executor
from platform_ai.skills.skill_metrics import skill_metrics
from platform_ai.skills.skill_permissions import skill_permissions
from platform_ai.skills.skill_registry import skill_registry

logger = logging.getLogger(__name__)


class SkillManager:
    def __init__(self) -> None:
        self._initialized = False

    def reset(self) -> None:
        skill_registry.reset()
        skill_cache.reset()
        skill_metrics.reset()
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        from platform_ai.skills import builtin

        builtin.register_all()
        self._initialized = True
        logger.info("skill_manager_initialized skills=%d", len(skill_registry.list_records()))

    def register(self, skill_cls: Type[AISkill]) -> SkillRecord:
        return skill_registry.register(skill_cls)

    async def load(self, skill_id: str) -> SkillRecord:
        self.initialize()
        record = skill_registry.get_record(skill_id)
        skill_cls = skill_registry.get_class(skill_id)
        instance = skill_cls()
        ctx = SkillContext(skill_id=skill_id, input={})
        try:
            instance.validate(ctx)
        except SkillValidationError:
            pass
        record.state = SkillState.LOADED
        record.loaded_at = datetime.now(timezone.utc).isoformat()
        await publish_skill_event(SkillLoadedEvent(skill_id=skill_id, version=record.metadata.version))
        return record

    def validate(self, skill_id: str, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        skill_cls = skill_registry.get_class(skill_id)
        instance = skill_cls()
        ctx = SkillContext(skill_id=skill_id, input=dict(input_data or {}))
        instance.validate(ctx)
        return {"valid": True, "skill_id": skill_id, "estimated_cost": instance.estimate_cost(ctx)}

    async def execute(self, request: SkillExecutionRequest, *, extra_context: dict[str, Any] | None = None) -> SkillExecutionResult:
        self.initialize()
        record = skill_registry.get_record(request.skill_id)
        await skill_permissions.check(record.metadata, plugin_id=request.plugin_id)
        if record.state == SkillState.REGISTERED:
            await self.load(request.skill_id)
        return await skill_executor.execute(request, extra_context=extra_context)

    async def disable(self, skill_id: str) -> SkillRecord:
        record = skill_registry.get_record(skill_id)
        record.metadata.enabled = False
        record.state = SkillState.DISABLED
        skill_cache.invalidate(skill_id)
        await publish_skill_event(SkillDisabledEvent(skill_id=skill_id))
        return record

    async def enable(self, skill_id: str) -> SkillRecord:
        record = skill_registry.get_record(skill_id)
        record.metadata.enabled = True
        return await self.load(skill_id)

    async def reload(self, skill_id: str) -> SkillRecord:
        skill_cache.invalidate(skill_id)
        return await self.load(skill_id)

    async def health(self, skill_id: str | None = None) -> dict[str, Any]:
        self.initialize()
        if skill_id:
            skill_cls = skill_registry.get_class(skill_id)
            instance = skill_cls()
            result = await instance.health()
            metrics = skill_metrics.for_skill(skill_id)
            return {**result.to_dict(), "metrics": metrics}
        results = []
        for record in skill_registry.list_records():
            try:
                skill_cls = skill_registry.get_class(record.skill_id)
                h = await skill_cls().health()
                results.append({**h.to_dict(), "state": record.state.value, "metrics": skill_metrics.for_skill(record.skill_id)})
            except Exception as exc:
                results.append({"skill_id": record.skill_id, "status": "unhealthy", "message": str(exc)})
        return {"skills": results, "total": len(results)}

    def list_skills(self) -> list[dict[str, Any]]:
        self.initialize()
        return [r.to_dict() for r in skill_registry.list_records()]

    def estimate_cost(self, skill_id: str, input_data: dict[str, Any] | None = None) -> float:
        skill_cls = skill_registry.get_class(skill_id)
        ctx = SkillContext(skill_id=skill_id, input=dict(input_data or {}))
        return skill_cls().estimate_cost(ctx)

    def metrics(self, skill_id: str | None = None) -> dict[str, Any]:
        if skill_id:
            return skill_metrics.for_skill(skill_id)
        return skill_metrics.summary()

    def summary(self) -> dict[str, Any]:
        self.initialize()
        return skill_registry.summary()


skill_manager = SkillManager()
