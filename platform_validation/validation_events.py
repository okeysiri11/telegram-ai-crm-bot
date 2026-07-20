# Validation layer events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class PlatformValidatedEvent(BaseEvent):
    report_id: str = ""
    status: str = ""
    check_count: int = 0
    duration_ms: float = 0.0


@dataclass(kw_only=True)
class ProductionReadyEvent(BaseEvent):
    platform_version: str = ""
    platform_status: str = ""
    score: float = 0.0
