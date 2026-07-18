# Workflow step handlers — each step type executes via skills or context.

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from platform_ai.skills.models import SkillExecutionRequest
from platform_ai.skills.skill_manager import skill_manager
from platform_ai.workflows.exceptions import StepExecutionError, WorkflowCancelledError, WorkflowTimeoutError
from platform_ai.workflows.models import StepResult, StepType, WorkflowStep
from platform_ai.workflows.workflow_context import WorkflowContext

logger = logging.getLogger(__name__)


class StepRunner:
    """Executes individual workflow steps."""

    async def run(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        *,
        plugin_id: str | None,
        user_id: str | None,
        use_cache: bool,
        is_cancelled: Any,
        **extra: Any,
    ) -> StepResult:
        if is_cancelled():
            raise WorkflowCancelledError("Workflow cancelled")
        start = time.perf_counter()
        handler = _HANDLERS.get(step.step_type)
        if handler is None:
            raise StepExecutionError(step.step_id, f"Unknown step type: {step.step_type}")
        try:
            coro = handler(
                self,
                step,
                ctx,
                plugin_id=plugin_id,
                user_id=user_id,
                use_cache=use_cache,
                **extra,
            )
            if step.timeout_seconds:
                output = await asyncio.wait_for(coro, timeout=step.timeout_seconds)
            else:
                output = await coro
        except asyncio.TimeoutError as exc:
            raise WorkflowTimeoutError(f"Step {step.step_id} timed out") from exc
        latency = (time.perf_counter() - start) * 1000
        cost = float(output.pop("_cost_usd", 0.0)) if isinstance(output, dict) else 0.0
        return StepResult(
            step_id=step.step_id,
            step_type=step.step_type,
            success=True,
            output=output if isinstance(output, dict) else {"result": output},
            latency_ms=latency,
            cost_usd=cost,
        )

    async def run_skill(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        *,
        plugin_id: str | None,
        user_id: str | None,
        use_cache: bool,
    ) -> dict[str, Any]:
        cfg = step.config
        skill_id = cfg["skill_id"]
        input_data = ctx.resolve_mapping(cfg.get("input_mapping", {}))
        if not input_data and cfg.get("input"):
            input_data = ctx.resolve_mapping(cfg["input"])
        request = SkillExecutionRequest(
            skill_id=skill_id,
            input=input_data,
            plugin_id=plugin_id,
            user_id=user_id,
            use_cache=use_cache,
        )
        result = await skill_manager.execute(
            request,
            extra_context={
                "workflow": {"workflow_id": ctx.workflow_id, "execution_id": ctx.execution_id},
                "conversation": ctx.conversation,
                "history": ctx.history,
                "files": ctx.files,
                "configuration": ctx.configuration,
            },
        )
        output = dict(result.output)
        output["_cost_usd"] = result.cost_usd
        output_key = cfg.get("output_key", step.step_id)
        ctx.set_memory(output_key, output)
        ctx.step_results[step.step_id] = {"output": output, "success": result.success}
        return output

    async def run_condition(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        **_: Any,
    ) -> dict[str, Any]:
        expr = step.config.get("expression", "true")
        result = _eval_expression(expr, ctx)
        return {"result": result, "_branch": "true" if result else "false"}

    async def run_branch(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        **_: Any,
    ) -> dict[str, Any]:
        field_name = step.config.get("field", "")
        value = ctx.resolve(field_name) if field_name.startswith("$") else ctx.memory.get(field_name)
        mapping = step.config.get("cases", {})
        branch = mapping.get(str(value), step.config.get("default"))
        return {"branch": branch, "value": value, "_next_override": branch}

    async def run_loop(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        *,
        plugin_id: str | None,
        user_id: str | None,
        use_cache: bool,
    ) -> dict[str, Any]:
        items_ref = step.config.get("items", "$input.items")
        items = ctx.resolve(items_ref) if isinstance(items_ref, str) and items_ref.startswith("$") else items_ref
        if not isinstance(items, list):
            items = []
        body_step = step.config.get("body_step")
        results: list[Any] = []
        for i, item in enumerate(items):
            ctx.memory["_loop_index"] = i
            ctx.memory["_loop_item"] = item
            if body_step:
                body = WorkflowStep(step_id=f"{step.step_id}_iter_{i}", step_type=StepType.SKILL.value, config=body_step)
                r = await self.run_skill(body, ctx, plugin_id=plugin_id, user_id=user_id, use_cache=use_cache)
                results.append(r)
        ctx.set_memory(step.config.get("output_key", f"{step.step_id}_results"), results)
        return {"count": len(results), "results": results}

    async def run_transform(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        **_: Any,
    ) -> dict[str, Any]:
        mapping = step.config.get("mapping", {})
        output = ctx.resolve_mapping(mapping)
        output_key = step.config.get("output_key", step.step_id)
        ctx.set_memory(output_key, output)
        return output

    async def run_merge(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        **_: Any,
    ) -> dict[str, Any]:
        keys = step.config.get("keys", [])
        merged: dict[str, Any] = {}
        for key in keys:
            val = ctx.memory.get(key) or ctx.get_step_output(key)
            if isinstance(val, dict):
                merged.update(val)
            else:
                merged[key] = val
        output_key = step.config.get("output_key", step.step_id)
        ctx.set_memory(output_key, merged)
        return merged

    async def run_parallel(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        *,
        plugin_id: str | None,
        user_id: str | None,
        use_cache: bool,
        parallel_steps: dict[str, WorkflowStep] | None = None,
        executor_fn: Any = None,
    ) -> dict[str, Any]:
        branch_ids = step.branches or step.config.get("branches", [])
        if not branch_ids or not parallel_steps or not executor_fn:
            return {"branches": branch_ids, "results": {}}

        async def _run_branch(bid: str) -> tuple[str, StepResult]:
            branch_step = parallel_steps[bid]
            result = await executor_fn(branch_step)
            return bid, result

        results_list = await asyncio.gather(*[_run_branch(b) for b in branch_ids], return_exceptions=True)
        results: dict[str, Any] = {}
        total_cost = 0.0
        for item in results_list:
            if isinstance(item, Exception):
                raise StepExecutionError(step.step_id, str(item)) from item
            bid, step_result = item
            results[bid] = step_result.to_dict()
            total_cost += step_result.cost_usd
            ctx.step_results[bid] = {"output": step_result.output, "success": step_result.success}
        ctx.set_memory(step.config.get("output_key", f"{step.step_id}_parallel"), results)
        return {"results": results, "_cost_usd": total_cost}

    async def run_approval(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        **_: Any,
    ) -> dict[str, Any]:
        auto_approve = step.config.get("auto_approve", True)
        message = step.config.get("message", "Approval required")
        approved = auto_approve or ctx.configuration.get("auto_approve", False)
        return {"approved": approved, "message": message, "_paused": not approved}

    async def run_plugin(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        **_: Any,
    ) -> dict[str, Any]:
        action = step.config.get("action", "noop")
        payload = ctx.resolve_mapping(step.config.get("payload", {}))
        return {"action": action, "payload": payload, "status": "ok"}

    async def run_delay(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        **_: Any,
    ) -> dict[str, Any]:
        seconds = float(step.config.get("seconds", 0))
        await asyncio.sleep(min(seconds, 30.0))
        return {"delayed_seconds": seconds}

    async def run_event(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        **_: Any,
    ) -> dict[str, Any]:
        event_type = step.config.get("event_type", "workflow.step.event")
        payload = ctx.resolve_mapping(step.config.get("payload", {}))
        logger.info("workflow_event step=%s type=%s payload=%s", step.step_id, event_type, payload)
        return {"event_type": event_type, "published": True, "payload": payload}


_HANDLERS = {
    StepType.SKILL.value: StepRunner.run_skill,
    StepType.CONDITION.value: StepRunner.run_condition,
    StepType.BRANCH.value: StepRunner.run_branch,
    StepType.LOOP.value: StepRunner.run_loop,
    StepType.TRANSFORM.value: StepRunner.run_transform,
    StepType.MERGE.value: StepRunner.run_merge,
    StepType.PARALLEL.value: StepRunner.run_parallel,
    StepType.APPROVAL.value: StepRunner.run_approval,
    StepType.PLUGIN.value: StepRunner.run_plugin,
    StepType.DELAY.value: StepRunner.run_delay,
    StepType.EVENT.value: StepRunner.run_event,
}


def _eval_expression(expr: str, ctx: WorkflowContext) -> bool:
    if expr.startswith("$"):
        val = ctx.resolve(expr)
        return bool(val)
    lowered = expr.lower().strip()
    if lowered in ("true", "1", "yes"):
        return True
    if lowered in ("false", "0", "no"):
        return False
    if "==" in expr:
        left, right = expr.split("==", 1)
        left_val = ctx.resolve(left.strip()) if left.strip().startswith("$") else left.strip().strip("'\"")
        right_val = ctx.resolve(right.strip()) if right.strip().startswith("$") else right.strip().strip("'\"")
        return str(left_val) == str(right_val)
    return bool(expr)


step_runner = StepRunner()
