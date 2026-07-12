# Rule-based workflow engine over workflow_rules / workflow_logs.

import json
from typing import Callable

_ACTION_HANDLERS: dict[str, Callable] = {}


class WorkflowEngine:
    @staticmethod
    def register_action(action_type: str, handler: Callable) -> None:
        _ACTION_HANDLERS[action_type] = handler

    @staticmethod
    def register_trigger(
        trigger_code: str,
        action_type: str,
        module: str = "system",
        action_payload: str = None,
    ) -> int:
        from database import register_workflow_rule
        return register_workflow_rule(trigger_code, action_type, module, action_payload)

    @staticmethod
    def execute_workflow(
        trigger_code: str,
        user_id: int,
        module: str,
        entity_type: str = None,
        entity_id: int = None,
        payload: dict = None,
    ) -> list[int]:
        from database import get_workflow_rules, log_workflow_execution

        payload = payload or {}
        log_ids = []
        rules = get_workflow_rules(trigger_code=trigger_code)

        for _rule_id, _trigger, rule_module, action_type, action_payload, _active in rules:
            try:
                merged = payload.copy()
                if action_payload:
                    merged.update(json.loads(action_payload))
                handler = _ACTION_HANDLERS.get(action_type, _default_send_notification)
                handler(
                    user_id=user_id,
                    module=rule_module or module,
                    trigger_code=trigger_code,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    payload=merged,
                )
                log_id = log_workflow_execution(
                    trigger_code,
                    user_id,
                    rule_module or module,
                    action_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    status="OK",
                )
                log_ids.append(log_id)
            except Exception as exc:
                log_id = log_workflow_execution(
                    trigger_code,
                    user_id,
                    rule_module or module,
                    action_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    status="ERROR",
                    details=str(exc),
                )
                log_ids.append(log_id)
        return log_ids


def _default_send_notification(
    user_id: int,
    module: str,
    trigger_code: str,
    entity_type: str = None,
    entity_id: int = None,
    payload: dict = None,
) -> int:
    from services.notifications import NotificationService

    payload = payload or {}
    title = payload.get("title") or f"Событие: {trigger_code}"
    message = payload.get("message") or ""
    if entity_type and entity_id:
        message = message or f"{entity_type} #{entity_id}"
    priority = payload.get("priority", "NORMAL")
    return NotificationService.create_notification(
        user_id=user_id,
        module=module,
        event_type=trigger_code,
        title=title,
        message=message,
        priority=priority,
        channel="SYSTEM",
    )


WorkflowEngine.register_action("send_notification", _default_send_notification)


def _action_create_task(
    user_id: int,
    module: str,
    trigger_code: str,
    entity_type: str = None,
    entity_id: int = None,
    payload: dict = None,
) -> int:
    from services.tasks import TaskService
    payload = payload or {}
    title = payload.get("title") or f"Workflow task: {trigger_code}"
    return TaskService.create(
        task_type=TaskService.WORKFLOW,
        creator_id=user_id,
        title=title,
        description=payload.get("message", ""),
        module=module,
        priority=payload.get("priority", "NORMAL"),
        assigned_user_id=payload.get("manager_id"),
    )


def _action_create_calendar_event(
    user_id: int,
    module: str,
    trigger_code: str,
    entity_type: str = None,
    entity_id: int = None,
    payload: dict = None,
) -> int:
    from services.calendar_service import CalendarService
    from datetime import datetime
    payload = payload or {}
    title = payload.get("title") or f"Event: {trigger_code}"
    owner = payload.get("manager_id") or user_id
    return CalendarService.create_event(
        creator_id=user_id,
        title=title,
        start_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        module=module,
        event_type=payload.get("event_type", "agro_task"),
        owner_id=owner,
        description=payload.get("message", ""),
    )


def _action_notify_client(
    user_id: int,
    module: str,
    trigger_code: str,
    entity_type: str = None,
    entity_id: int = None,
    payload: dict = None,
) -> int:
    from services.notifications import NotificationService
    payload = payload or {}
    client_id = payload.get("client_id")
    if not client_id:
        return 0
    return NotificationService.create_notification(
        user_id=client_id,
        module=module,
        title=payload.get("title", "Обновление заявки"),
        message=payload.get("message", ""),
        priority=payload.get("priority", "NORMAL"),
        event_type=trigger_code,
    )


def _action_notify_participants(
    user_id: int,
    module: str,
    trigger_code: str,
    entity_type: str = None,
    entity_id: int = None,
    payload: dict = None,
) -> int:
    from services.notifications import NotificationService
    payload = payload or {}
    ids = {user_id}
    if payload.get("client_id"):
        ids.add(payload["client_id"])
    if payload.get("manager_id"):
        ids.add(payload["manager_id"])
    last_id = 0
    for uid in ids:
        last_id = NotificationService.create_notification(
            user_id=uid,
            module=module,
            title=payload.get("title", "Обновление заявки"),
            message=payload.get("message", ""),
            priority=payload.get("priority", "NORMAL"),
            event_type=trigger_code,
        )
    return last_id


WorkflowEngine.register_action("create_task", _action_create_task)
WorkflowEngine.register_action("create_calendar_event", _action_create_calendar_event)
WorkflowEngine.register_action("notify_client", _action_notify_client)
WorkflowEngine.register_action("notify_participants", _action_notify_participants)
