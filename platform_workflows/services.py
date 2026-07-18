# Service registry — all workflow service calls route through here.

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from platform_workflows.context import WorkflowContext

logger = logging.getLogger(__name__)

ServiceHandler = Callable[..., Awaitable[Any] | Any]

_REGISTRY: dict[str, ServiceHandler] = {}


def register_service(name: str, handler: ServiceHandler) -> None:
    _REGISTRY[name.lower()] = handler


def get_service(name: str) -> ServiceHandler | None:
    return _REGISTRY.get(name.lower())


def list_services() -> list[str]:
    return sorted(_REGISTRY.keys())


async def invoke_service(
    service_name: str,
    method_name: str,
    context: WorkflowContext,
    params: dict[str, Any] | None = None,
) -> Any:
    handler = get_service(service_name)
    if handler is None:
        raise ValueError(f"Unknown workflow service: {service_name}")
    logger.info(
        "workflow_service_call service=%s method=%s execution=%s",
        service_name,
        method_name,
        context.execution_id,
    )
    return await handler(method_name, context, **(params or {}))


def _resolve_params(params: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, str) and value.startswith("$"):
            out[key] = context.resolve(value)
        elif isinstance(value, dict):
            out[key] = _resolve_params(value, context)
        else:
            out[key] = value
    return out


async def invoke_from_step_config(step_config: dict[str, Any], context: WorkflowContext) -> Any:
    service_name = str(step_config.get("service") or "")
    method_name = str(step_config.get("method") or "")
    params = _resolve_params(dict(step_config.get("params") or {}), context)
    return await invoke_service(service_name, method_name, context, params)


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

    for name in (
        "RequestService",
        "ManagerService",
        "SmartAssignmentService",
        "NotificationService",
        "AuditService",
        "KpiService",
        "EscalationService",
    ):
        register_service(name, _dispatch)


_register_default_services()
