# Manager pool events — assignment lifecycle for dynamic pool.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class ManagerAssignedEvent(BaseEvent):
    """Pool manager selected for a vertical."""

    pool_manager_id: str
    manager_id: str | None = None
    manager_telegram_id: int
    manager_name: str
    vertical: str
    assignment_mode: str = "ROUND_ROBIN"
    request_id: str | None = None
    request_number: str | None = None


@dataclass(kw_only=True)
class ManagerReleasedEvent(BaseEvent):
    pool_manager_id: str
    manager_telegram_id: int
    manager_name: str
    vertical: str
    request_id: str | None = None
    request_number: str | None = None
    previous_load: int = 0
    new_load: int = 0


@dataclass(kw_only=True)
class ManagerUnavailableEvent(BaseEvent):
    vertical: str
    reason: str = "no_active_managers"
    assignment_mode: str = "ROUND_ROBIN"
