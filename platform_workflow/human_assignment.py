# Human task assignment — Manager, Administrator, Operator, Owner.

from __future__ import annotations

import logging
from typing import Callable

from platform_workflow.exceptions import HumanAssignmentError
from platform_workflow.models import HumanRole

logger = logging.getLogger(__name__)

HumanAssigneeResolver = Callable[[HumanRole, dict], str | None]


class HumanAssignmentService:
    """Assign tasks to human roles with notification support."""

    def __init__(self) -> None:
        self._resolvers: dict[HumanRole, HumanAssigneeResolver] = {}
        self._default_assignees: dict[HumanRole, str] = {
            HumanRole.MANAGER: "manager_default",
            HumanRole.ADMINISTRATOR: "admin_default",
            HumanRole.OPERATOR: "operator_default",
            HumanRole.OWNER: "owner_default",
        }
        self._notifications: list[dict] = []

    def reset(self) -> None:
        self._notifications.clear()

    def register_resolver(self, role: HumanRole, resolver: HumanAssigneeResolver) -> None:
        self._resolvers[role] = resolver

    def set_default_assignee(self, role: HumanRole, assignee_id: str) -> None:
        self._default_assignees[role] = assignee_id

    def assign(self, role: HumanRole, context: dict | None = None) -> str:
        ctx = context or {}
        resolver = self._resolvers.get(role)
        if resolver:
            assignee = resolver(role, ctx)
            if assignee:
                return assignee
        default = self._default_assignees.get(role)
        if not default:
            raise HumanAssignmentError(role.value, f"No assignee configured for role {role.value}")
        logger.info("human_assigned role=%s assignee=%s", role.value, default)
        return default

    async def notify(self, assignee_id: str, task_id: str, message: str, *, channel: str = "internal") -> None:
        notification = {
            "assignee_id": assignee_id,
            "task_id": task_id,
            "message": message,
            "channel": channel,
        }
        self._notifications.append(notification)
        logger.info("human_notification task=%s assignee=%s", task_id, assignee_id)

    def notifications(self) -> list[dict]:
        return list(self._notifications)


human_assignment_service = HumanAssignmentService()
