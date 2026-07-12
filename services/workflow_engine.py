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
