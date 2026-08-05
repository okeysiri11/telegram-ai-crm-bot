"""Domain adapters package — Sprint 34.2C."""

from platform_state.adapters.domain import (
    calendar_adapter,
    conversation_adapter,
    crm_adapter,
    file_adapter,
    memory_facade,
    notification_adapter,
    task_adapter,
    workspace_adapter,
)

__all__ = [
    "task_adapter",
    "calendar_adapter",
    "notification_adapter",
    "conversation_adapter",
    "memory_facade",
    "file_adapter",
    "crm_adapter",
    "workspace_adapter",
]
