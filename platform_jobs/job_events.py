# Job Engine events — published to Platform EventBus.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class JobCreatedEvent(BaseEvent):
    job_id: str
    job_type: str
    handler_name: str


@dataclass(kw_only=True)
class JobStartedEvent(BaseEvent):
    job_id: str
    handler_name: str
    worker_id: str = ""


@dataclass(kw_only=True)
class JobCompletedEvent(BaseEvent):
    job_id: str
    handler_name: str
    duration_ms: float = 0.0


@dataclass(kw_only=True)
class JobFailedEvent(BaseEvent):
    job_id: str
    handler_name: str
    error: str
    retry_count: int = 0


@dataclass(kw_only=True)
class JobRetriedEvent(BaseEvent):
    job_id: str
    handler_name: str
    attempt: int
    next_run_at: float


@dataclass(kw_only=True)
class JobCancelledEvent(BaseEvent):
    job_id: str
    handler_name: str
    reason: str = ""
