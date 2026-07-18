# WorkflowExecutor — execute individual workflow steps (no direct SQL).

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Awaitable, Callable

from events.event_bus import publish
from workflow.models import StepDefinition, StepType
from workflow.workflow_context import WorkflowContext

logger = logging.getLogger(__name__)

ServiceHandler = Callable[..., Awaitable[Any] | Any]

_SERVICE_REGISTRY: dict[str, ServiceHandler] = {}


def register_service(name: str, handler: ServiceHandler) -> None:
    _SERVICE_REGISTRY[name.lower()] = handler


def _resolve_path(context: WorkflowContext, path: str) -> Any:
    """Resolve dotted path: variables.vin, request.id, telegram_user.id"""
    parts = path.strip().split(".")
    if not parts:
        return None
    root_name = parts[0]
    mapping = {
        "variables": context.variables,
        "request": context.request,
        "manager": context.manager,
        "telegram_user": context.telegram_user,
        "metadata": context.metadata,
        "fsm": context.fsm,
    }
    current: Any = mapping.get(root_name, context.variables.get(root_name))
    for part in parts[1:]:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def evaluate_condition(expression: str, context: WorkflowContext) -> bool:
    """Evaluate simple conditions: vin == yes, variables.count > 3"""
    expr = expression.strip()
    if not expr:
        return False

    match = re.match(
        r"^(?:(variables|request|manager|telegram_user|metadata|fsm)\.)?(\w+)\s*(==|!=|>=|<=|>|<)\s*(.+)$",
        expr,
    )
    if not match:
        # Bare variable truthiness: "vin" means variables.vin is truthy
        value = _resolve_path(context, expr) if "." in expr else context.variables.get(expr)
        return bool(value)

    prefix, key, op, raw_rhs = match.groups()
    lhs_path = f"{prefix}.{key}" if prefix else key
    lhs = _resolve_path(context, lhs_path) if prefix else context.variables.get(key)
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


class WorkflowExecutor:
    @staticmethod
    async def execute_step(
        step: StepDefinition,
        context: WorkflowContext,
        *,
        user_input: Any | None = None,
        callback_data: str | None = None,
    ) -> tuple[WorkflowContext, str | None, bool]:
        """
        Execute one step.

        Returns (context, next_step_id, should_pause).
        """
        if step.type in {StepType.INPUT, StepType.QUESTION, StepType.MEDIA}:
            var_name = step.config.get("variable") or step.id
            if user_input is not None:
                context.set_variable(var_name, user_input)
            else:
                from workflow.models import ExecutionStatus

                context.status = ExecutionStatus.WAITING
                context.current_step = step.id
                context.touch()
                return context, step.id, True

        if step.type == StepType.CALLBACK:
            if callback_data is not None:
                var_name = step.config.get("variable") or step.id
                context.set_variable(var_name, callback_data)
            else:
                from workflow.models import ExecutionStatus

                context.status = ExecutionStatus.WAITING
                context.current_step = step.id
                context.touch()
                return context, step.id, True

        if step.type == StepType.CHOICE:
            var_name = str(step.config.get("variable") or step.id)
            value = user_input or callback_data or context.variables.get(var_name)
            if value is None:
                from workflow.models import ExecutionStatus

                context.status = ExecutionStatus.WAITING
                context.current_step = step.id
                context.touch()
                return context, step.id, True
            context.set_variable(var_name, value)
            options = step.config.get("options") or {}
            next_step = options.get(str(value)) or step.next_step
            context.current_step = step.id
            context.touch()
            return context, next_step, False

        if step.type == StepType.CONDITION:
            when = str(step.config.get("when") or "")
            result = evaluate_condition(when, context)
            branch = step.config.get("then") if result else step.config.get("else")
            next_step = str(branch) if branch else step.next_step
            context.current_step = step.id
            context.touch()
            return context, next_step, False

        if step.type == StepType.SERVICE:
            await WorkflowExecutor._run_service(step, context)
            context.current_step = step.id
            context.touch()
            return context, step.next_step, False

        if step.type == StepType.EVENT:
            await WorkflowExecutor._publish_event(step, context)
            context.current_step = step.id
            context.touch()
            return context, step.next_step, False

        if step.type == StepType.DELAY:
            seconds = float(step.config.get("seconds") or 0)
            if seconds > 0:
                await asyncio.sleep(min(seconds, 30.0))
            context.current_step = step.id
            context.touch()
            return context, step.next_step, False

        if step.type == StepType.COMPLETE:
            from workflow.models import ExecutionStatus

            context.status = ExecutionStatus.COMPLETED
            context.completed_at = context.updated_at
            context.current_step = step.id
            context.touch()
            return context, None, False

        # callback without user data falls through to waiting above; default passthrough
        context.current_step = step.id
        context.touch()
        return context, step.next_step, False

    @staticmethod
    async def _run_service(step: StepDefinition, context: WorkflowContext) -> Any:
        service_name = str(step.config.get("service") or "").lower()
        method_name = str(step.config.get("method") or "")
        handler = _SERVICE_REGISTRY.get(service_name)
        if handler is None:
            raise ValueError(f"Unknown workflow service: {service_name}")

        params = dict(step.config.get("params") or {})
        # Template substitution from context
        resolved = WorkflowExecutor._resolve_params(params, context)
        logger.info(
            "workflow_service_call service=%s method=%s execution=%s",
            service_name,
            method_name,
            context.execution_id,
        )
        return await handler(method_name, context, **resolved)

    @staticmethod
    def _resolve_params(params: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                out[key] = _resolve_path(context, value[1:])
            elif isinstance(value, dict):
                out[key] = WorkflowExecutor._resolve_params(value, context)
            else:
                out[key] = value
        return out

    @staticmethod
    async def _publish_event(step: StepDefinition, context: WorkflowContext) -> None:
        event_type = str(step.config.get("event_type") or "")
        payload = dict(step.config.get("payload") or {})
        resolved = WorkflowExecutor._resolve_params(payload, context)

        from events.request_events import RequestCreatedEvent
        from events.workflow_events import WorkflowStepCompletedEvent

        event_map = {
            "RequestCreatedEvent": RequestCreatedEvent,
            "WorkflowStepCompletedEvent": WorkflowStepCompletedEvent,
        }
        cls = event_map.get(event_type)
        if cls is None:
            logger.info("workflow_event_skipped type=%s execution=%s", event_type, context.execution_id)
            return

        await publish(cls(**resolved))


def _register_default_services() -> None:
    async def _dispatch(method: str, context: WorkflowContext, **kwargs: Any) -> Any:
        if method == "create_request":
            from services.request_service import RequestService

            vertical = kwargs.get("vertical") or context.vertical.lower()
            telegram_id = kwargs.get("client_telegram_id") or context.telegram_user.get("id")
            result = await RequestService.create_request(
                vertical=vertical,
                client_telegram_id=int(telegram_id),
                client_name=str(kwargs.get("client_name") or context.telegram_user.get("name") or ""),
                client_username=context.telegram_user.get("username"),
                description=str(kwargs.get("description") or context.variables.get("description") or ""),
                request_type=kwargs.get("request_type"),
            )
            context.request = dict(result)
            return result

        if method == "assign_manager":
            from services.manager_service import manager_service

            vertical = kwargs.get("vertical") or context.vertical.lower()
            mgr = await manager_service.resolve_manager_for_vertical(
                vertical,
                request_type=kwargs.get("request_type"),
                request_id=context.request.get("id"),
                request_number=context.request.get("request_number"),
            )
            if mgr:
                context.manager = dict(mgr)
            return mgr

        if method == "smart_assign":
            from services.smart_assignment_service import smart_assignment_service

            vertical = kwargs.get("vertical") or context.vertical.lower()
            mgr = await smart_assignment_service.assign_for_request(
                vertical=vertical,
                request_type=kwargs.get("request_type"),
                request_id=context.request.get("id"),
                request_number=context.request.get("request_number"),
            )
            if mgr:
                context.manager = dict(mgr)
            return mgr

        if method == "notify":
            from services.notification_service import notification_service

            return await notification_service.notify_managers_new_request(
                vertical=str(kwargs.get("vertical") or context.vertical.lower()),
                request_number=str(kwargs.get("request_number") or context.request.get("request_number") or ""),
                client_name=str(kwargs.get("client_name") or context.telegram_user.get("name") or ""),
                product=str(kwargs.get("product") or context.variables.get("description") or ""),
                manager_telegram_id=context.manager.get("telegram_id"),
            )

        if method == "audit":
            from audit.audit_event import AuditRecord
            from audit.audit_service import AuditService

            record = AuditRecord(
                event_type="WORKFLOW_STEP",
                entity_type="workflow_execution",
                entity_id=context.execution_id,
                actor_id=str(context.telegram_user.get("id")) if context.telegram_user.get("id") else None,
                old_value=None,
                new_value={
                    "workflow_id": context.workflow_id,
                    "step_id": kwargs.get("step_id") or context.current_step,
                },
                metadata_json=dict(kwargs),
            )
            return await AuditService.record(record)

        if method == "kpi_invalidate":
            from services.kpi_service import kpi_service

            kpi_service.invalidate_cache()
            return None

        raise ValueError(f"Unknown service method: {method}")

    register_service("RequestService", _dispatch)
    register_service("ManagerService", _dispatch)
    register_service("SmartAssignmentService", _dispatch)
    register_service("NotificationService", _dispatch)
    register_service("AuditService", _dispatch)
    register_service("KpiService", _dispatch)
    register_service("EscalationService", _dispatch)


_register_default_services()
