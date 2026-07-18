# Skill executor — runs skills via AI Platform (never direct provider access).

from __future__ import annotations

import logging
import time
from typing import Any

from platform_ai.ai_service import ai_service
from platform_ai.models import AIRequest
from platform_ai.skills.exceptions import SkillDisabledError, SkillExecutionError
from platform_ai.skills.models import SkillExecutionRequest, SkillExecutionResult, SkillState
from platform_ai.skills.skill_base import AISkill
from platform_ai.skills.skill_cache import skill_cache
from platform_ai.skills.skill_context import SkillContext
from platform_ai.skills.skill_events import SkillCostUpdatedEvent, SkillExecutedEvent, SkillFailedEvent, publish_skill_event
from platform_ai.skills.skill_metrics import skill_metrics
from platform_ai.skills.skill_registry import skill_registry

logger = logging.getLogger(__name__)


class SkillExecutor:
    async def execute(self, request: SkillExecutionRequest, *, extra_context: dict[str, Any] | None = None) -> SkillExecutionResult:
        record = skill_registry.get_record(request.skill_id)
        if record.state == SkillState.DISABLED or not record.metadata.enabled:
            raise SkillDisabledError(f"Skill disabled: {request.skill_id}")

        skill_cls = skill_registry.get_class(request.skill_id)
        skill = skill_cls()
        ctx = SkillContext.from_execution(
            request.skill_id,
            plugin_id=request.plugin_id,
            user_id=request.user_id,
            request_id=request.request_id,
            input_data=request.input,
            extra=extra_context,
        )

        skill.validate(ctx)

        meta = record.metadata
        if request.use_cache:
            cached = skill_cache.get(request.skill_id, request.input, meta.cache_ttl)
            if cached:
                skill_metrics.record(cached)
                return cached

        start = time.perf_counter()
        try:
            result = await self._run_skill(skill, ctx, request)
        except Exception as exc:
            latency = (time.perf_counter() - start) * 1000
            failed = SkillExecutionResult(
                skill_id=request.skill_id,
                execution_id=request.execution_id,
                success=False,
                latency_ms=latency,
                error=str(exc),
            )
            skill_metrics.record(failed)
            await publish_skill_event(
                SkillFailedEvent(
                    skill_id=request.skill_id,
                    execution_id=request.execution_id,
                    plugin_id=request.plugin_id or "",
                    error=str(exc),
                )
            )
            raise SkillExecutionError(str(exc)) from exc

        result.execution_id = request.execution_id
        result.latency_ms = (time.perf_counter() - start) * 1000

        if request.use_cache and result.success:
            skill_cache.set(request.skill_id, request.input, result, meta.cache_ttl)

        skill_metrics.record(result)
        await publish_skill_event(
            SkillExecutedEvent(
                skill_id=result.skill_id,
                execution_id=result.execution_id,
                plugin_id=request.plugin_id or "",
                latency_ms=result.latency_ms,
                cost_usd=result.cost_usd,
                cached=result.cached,
            )
        )
        await publish_skill_event(
            SkillCostUpdatedEvent(
                skill_id=result.skill_id,
                cost_usd=result.cost_usd,
                avg_cost_usd=skill_metrics.for_skill(result.skill_id).get("avg_cost_usd", 0.0),
            )
        )
        return result

    async def _run_skill(self, skill: AISkill, ctx: SkillContext, request: SkillExecutionRequest) -> SkillExecutionResult:
        skill_cls = type(skill)
        if getattr(skill_cls, "_uses_ai", True) is False:
            return await skill.execute(ctx)

        prompt = skill.build_prompt(ctx)
        ai_request = AIRequest(
            prompt=prompt,
            task_type=skill.task_type,
            plugin_id=request.plugin_id,
            template_id=skill.template_id,
            context=ctx.to_prompt_context(),
            use_cache=False,
        )
        if skill.preferred_models:
            ai_request.model = skill.preferred_models[0]

        response = await ai_service.complete(ai_request)
        output = skill.parse_output(response.content, ctx)

        return SkillExecutionResult(
            skill_id=skill.skill_id,
            execution_id=request.execution_id,
            success=True,
            output=output,
            raw_content=response.content,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost_usd=response.cost_usd,
            provider_id=response.provider_id,
            model_id=response.model_id,
        )


skill_executor = SkillExecutor()
