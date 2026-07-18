# WorkflowSteps — unified step execution (business, AI, control flow).

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any, Callable

from platform_workflows.context import WorkflowContext
from platform_workflows.exceptions import (
    StepExecutionError,
    WorkflowCancelledError,
    WorkflowTimeoutError,
)
from platform_workflows.models import ExecutionStatus, StepDefinition, StepResult, StepType
from platform_workflows.services import invoke_from_step_config

logger = logging.getLogger(__name__)


def evaluate_condition(expression: str, context: WorkflowContext) -> bool:
    expr = expression.strip()
    if not expr:
        return False

    match = re.match(
        r"^(?:(variables|request|manager|telegram_user|metadata|fsm|memory|input)\.)?(\w+)\s*(==|!=|>=|<=|>|<)\s*(.+)$",
        expr,
    )
    if not match:
        if expr.startswith("$"):
            return bool(context.resolve(expr))
        value = context.resolve(f"variables.{expr}") if "." in expr else context.variables.get(expr)
        return bool(value)

    prefix, key, op, raw_rhs = match.groups()
    lhs_path = f"${prefix}.{key}" if prefix else f"variables.{key}"
    lhs = context.resolve(lhs_path) if prefix else context.variables.get(key)
    rhs = raw_rhs.strip().strip("'\"")
    try:
        if rhs.lower() in {"true", "false"}:
            rhs_val: Any = rhs.lower() == "true"
        elif rhs.isdigit():
            rhs_val = int(rhs)
        else:
            rhs_val = rhs
    except Exception:
        rhs_val = rhs

    ops = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
    }
    try:
        return bool(ops[op](lhs, rhs_val))
    except Exception:
        return False


class WorkflowSteps:
    """Executes individual workflow steps for the unified engine."""

    async def execute(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        *,
        user_input: Any | None = None,
        callback_data: str | None = None,
        plugin_id: str | None = None,
        user_id: str | None = None,
        use_cache: bool = True,
        is_cancelled: Callable[[], bool] | None = None,
        all_steps: dict[str, StepDefinition] | None = None,
        executor_fn: Any = None,
    ) -> tuple[WorkflowContext, StepResult, str | None, bool]:
        if is_cancelled and is_cancelled():
            raise WorkflowCancelledError("Workflow cancelled")

        start = time.perf_counter()
        handler = _HANDLERS.get(step.type)
        if handler is None:
            raise StepExecutionError(step.id, f"Unknown step type: {step.type.value}")

        try:
            coro = handler(
                self,
                step,
                context,
                user_input=user_input,
                callback_data=callback_data,
                plugin_id=plugin_id or context.plugin_id,
                user_id=user_id or context.user_id,
                use_cache=use_cache,
                all_steps=all_steps,
                executor_fn=executor_fn,
            )
            timeout = step.timeout_seconds or step.config.get("timeout_seconds")
            if timeout:
                output, next_step, pause = await asyncio.wait_for(coro, timeout=float(timeout))
            else:
                output, next_step, pause = await coro
        except asyncio.TimeoutError as exc:
            raise WorkflowTimeoutError(f"Step {step.id} timed out") from exc

        latency = (time.perf_counter() - start) * 1000
        cost = float(output.pop("_cost_usd", 0.0)) if isinstance(output, dict) else 0.0
        context.cost_usd += cost
        result = StepResult(
            step_id=step.id,
            step_type=step.type.value,
            success=True,
            output=output if isinstance(output, dict) else {"result": output},
            latency_ms=latency,
            cost_usd=cost,
        )
        context.step_results[step.id] = result
        return context, result, next_step, pause

    async def run_interactive(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        *,
        user_input: Any | None = None,
        callback_data: str | None = None,
    ) -> tuple[dict[str, Any], str | None, bool]:
        if step.type in {StepType.INPUT, StepType.QUESTION, StepType.MEDIA}:
            var_name = step.config.get("variable") or step.id
            if user_input is not None:
                context.set_variable(var_name, user_input)
            else:
                context.status = ExecutionStatus.WAITING
                context.current_step = step.id
                context.touch()
                return {}, step.id, True

        if step.type == StepType.CALLBACK:
            if callback_data is not None:
                var_name = step.config.get("variable") or step.id
                context.set_variable(var_name, callback_data)
            else:
                context.status = ExecutionStatus.WAITING
                context.current_step = step.id
                context.touch()
                return {}, step.id, True

        if step.type == StepType.CHOICE:
            var_name = str(step.config.get("variable") or step.id)
            value = user_input or callback_data or context.variables.get(var_name)
            if value is None:
                context.status = ExecutionStatus.WAITING
                context.current_step = step.id
                context.touch()
                return {}, step.id, True
            context.set_variable(var_name, value)
            options = step.config.get("options") or {}
            next_step = options.get(str(value)) or step.next_step
            context.current_step = step.id
            context.touch()
            return {"value": value}, next_step, False

        if step.type == StepType.MEDIA and user_input is None:
            context.status = ExecutionStatus.WAITING
            context.current_step = step.id
            context.touch()
            return {}, step.id, True

        return {}, step.next_step, False

    async def run_condition(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        when = str(step.config.get("when") or step.config.get("expression") or "")
        result = evaluate_condition(when, context)
        branch = step.on_true or step.config.get("then") if result else step.on_false or step.config.get("else")
        next_step = str(branch) if branch else step.next_step
        return {"result": result, "_branch": "true" if result else "false"}, next_step, False

    async def run_branch(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        field_name = step.config.get("field", "")
        value = context.resolve(field_name) if str(field_name).startswith("$") else context.memory.get(field_name)
        mapping = step.config.get("cases", {})
        branch = mapping.get(str(value), step.config.get("default"))
        return {"branch": branch, "value": value, "_next_override": branch}, branch or step.next_step, False

    async def run_loop(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        *,
        plugin_id: str | None = None,
        user_id: str | None = None,
        use_cache: bool = True,
        all_steps: dict[str, StepDefinition] | None = None,
        executor_fn: Any = None,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        items_ref = step.config.get("items", "$input.items")
        items = context.resolve(items_ref) if isinstance(items_ref, str) and items_ref.startswith("$") else items_ref
        if not isinstance(items, list):
            items = []
        body_cfg = step.config.get("body_step")
        results: list[Any] = []
        for i, item in enumerate(items):
            context.memory["_loop_index"] = i
            context.memory["_loop_item"] = item
            if body_cfg and all_steps and executor_fn:
                body_id = f"{step.id}_iter_{i}"
                body = StepDefinition.from_dict({**body_cfg, "id": body_id, "step_id": body_id})
                _, step_result = await executor_fn(body)
                results.append(step_result.to_dict())
        output_key = step.config.get("output_key", f"{step.id}_results")
        context.set_memory(output_key, results)
        return {"count": len(results), "results": results}, step.next_step, False

    async def run_parallel(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        *,
        all_steps: dict[str, StepDefinition] | None = None,
        executor_fn: Any = None,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        branch_ids = step.branches or step.config.get("branches", [])
        if not branch_ids or not all_steps or not executor_fn:
            return {"branches": branch_ids, "results": {}}, step.next_step, False

        async def _run_branch(bid: str) -> tuple[str, StepResult]:
            branch_step = all_steps[bid]
            _, result = await executor_fn(branch_step)
            return bid, result

        results_list = await asyncio.gather(*[_run_branch(b) for b in branch_ids], return_exceptions=True)
        results: dict[str, Any] = {}
        total_cost = 0.0
        for item in results_list:
            if isinstance(item, Exception):
                raise StepExecutionError(step.id, str(item)) from item
            bid, step_result = item
            results[bid] = step_result.to_dict()
            total_cost += step_result.cost_usd
        context.set_memory(step.config.get("output_key", f"{step.id}_parallel"), results)
        return {"results": results, "_cost_usd": total_cost}, step.next_step, False

    async def run_service(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        await invoke_from_step_config(step.config, context)
        return {"service": step.config.get("service"), "method": step.config.get("method")}, step.next_step, False

    async def run_event(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        event_type = str(step.config.get("event_type") or "workflow.step.event")
        payload = context.resolve_mapping(dict(step.config.get("payload") or {}))
        from events.event_bus import publish
        from events.request_events import RequestCreatedEvent
        from events.workflow_events import WorkflowStepCompletedEvent

        event_map = {
            "RequestCreatedEvent": RequestCreatedEvent,
            "WorkflowStepCompletedEvent": WorkflowStepCompletedEvent,
        }
        cls = event_map.get(event_type)
        if cls is not None:
            await publish(cls(**payload))
        else:
            logger.info("workflow_event type=%s execution=%s", event_type, context.execution_id)
        return {"event_type": event_type, "published": True, "payload": payload}, step.next_step, False

    async def run_delay(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        seconds = float(step.config.get("seconds") or 0)
        if seconds > 0:
            await asyncio.sleep(min(seconds, 30.0))
        return {"delayed_seconds": seconds}, step.next_step, False

    async def run_skill(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        *,
        plugin_id: str | None = None,
        user_id: str | None = None,
        use_cache: bool = True,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        from platform_ai.skills.models import SkillExecutionRequest
        from platform_ai.skills.skill_manager import skill_manager

        cfg = step.config
        skill_id = cfg.get("skill_id") or cfg.get("skill")
        if not skill_id:
            raise StepExecutionError(step.id, "skill step requires skill_id")
        input_data = context.resolve_mapping(cfg.get("input_mapping", {}))
        if not input_data and cfg.get("input"):
            input_data = context.resolve_mapping(cfg["input"])
        request = SkillExecutionRequest(
            skill_id=str(skill_id),
            input=input_data,
            plugin_id=plugin_id,
            user_id=user_id,
            use_cache=use_cache,
        )
        result = await skill_manager.execute(
            request,
            extra_context={
                "workflow": {"workflow_id": context.workflow_id, "execution_id": context.execution_id},
                "conversation": context.conversation,
                "history": context.history,
                "files": context.files,
                "configuration": context.configuration,
            },
        )
        output = dict(result.output)
        output["_cost_usd"] = result.cost_usd
        output_key = cfg.get("output_key", step.id)
        context.set_memory(output_key, output)
        return output, step.next_step, False

    async def run_transform(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        mapping = step.config.get("mapping", {})
        output = context.resolve_mapping(mapping)
        output_key = step.config.get("output_key", step.id)
        context.set_memory(output_key, output)
        return output, step.next_step, False

    async def run_merge(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        keys = step.config.get("keys", [])
        merged: dict[str, Any] = {}
        for key in keys:
            val = context.memory.get(key) or context.get_step_output(key)
            if isinstance(val, dict):
                merged.update(val)
            else:
                merged[key] = val
        output_key = step.config.get("output_key", step.id)
        context.set_memory(output_key, merged)
        return merged, step.next_step, False

    async def run_approval(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        auto_approve = step.config.get("auto_approve", True)
        message = step.config.get("message", "Approval required")
        approved = auto_approve or context.configuration.get("auto_approve", False)
        if not approved:
            context.status = ExecutionStatus.PAUSED
            return {"approved": False, "message": message, "_paused": True}, step.id, True
        return {"approved": True, "message": message}, step.next_step, False

    async def run_plugin(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        action = step.config.get("action", "noop")
        payload = context.resolve_mapping(step.config.get("payload", {}))
        return {"action": action, "payload": payload, "status": "ok"}, step.next_step, False

    async def run_complete(
        self,
        step: StepDefinition,
        context: WorkflowContext,
        **_: Any,
    ) -> tuple[dict[str, Any], str | None, bool]:
        context.status = ExecutionStatus.COMPLETED
        context.completed_at = context.updated_at
        return {"completed": True}, None, False


_HANDLERS = {
    StepType.INPUT: lambda self, step, ctx, **kw: self.run_interactive(step, ctx, **kw),
    StepType.QUESTION: lambda self, step, ctx, **kw: self.run_interactive(step, ctx, **kw),
    StepType.MEDIA: lambda self, step, ctx, **kw: self.run_interactive(step, ctx, **kw),
    StepType.CALLBACK: lambda self, step, ctx, **kw: self.run_interactive(step, ctx, **kw),
    StepType.CHOICE: lambda self, step, ctx, **kw: self.run_interactive(step, ctx, **kw),
    StepType.CONDITION: WorkflowSteps.run_condition,
    StepType.BRANCH: WorkflowSteps.run_branch,
    StepType.LOOP: WorkflowSteps.run_loop,
    StepType.PARALLEL: WorkflowSteps.run_parallel,
    StepType.SERVICE: WorkflowSteps.run_service,
    StepType.EVENT: WorkflowSteps.run_event,
    StepType.DELAY: WorkflowSteps.run_delay,
    StepType.SKILL: WorkflowSteps.run_skill,
    StepType.AI: WorkflowSteps.run_skill,
    StepType.TRANSFORM: WorkflowSteps.run_transform,
    StepType.MERGE: WorkflowSteps.run_merge,
    StepType.APPROVAL: WorkflowSteps.run_approval,
    StepType.PLUGIN: WorkflowSteps.run_plugin,
    StepType.COMPLETE: WorkflowSteps.run_complete,
}

workflow_steps = WorkflowSteps()
