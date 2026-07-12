# Event Bus metrics — in-process counters + DB aggregates.

from __future__ import annotations

import time
from dataclasses import dataclass

from sqlalchemy import func, select

from database.models.crm_events import (
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_DEAD_LETTER,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_PENDING,
    Event,
)
from database.session import get_session


@dataclass
class EventBusMetrics:
    total_events: int = 0
    successful_events: int = 0
    failed_events: int = 0
    dead_letter_events: int = 0
    total_processing_time_ms: float = 0.0
    processing_samples: int = 0

    @property
    def average_processing_time(self) -> float:
        if self.processing_samples == 0:
            return 0.0
        return self.total_processing_time_ms / self.processing_samples


_metrics = EventBusMetrics()


def record_published() -> None:
    _metrics.total_events += 1


def record_success(processing_time_ms: float) -> None:
    _metrics.successful_events += 1
    _metrics.total_processing_time_ms += processing_time_ms
    _metrics.processing_samples += 1


def record_failure() -> None:
    _metrics.failed_events += 1


def record_dead_letter() -> None:
    _metrics.dead_letter_events += 1


class ProcessingTimer:
    def __enter__(self) -> ProcessingTimer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        elapsed_ms = (time.perf_counter() - self._start) * 1000
        record_success(elapsed_ms)


async def get_metrics() -> dict:
    async with get_session() as session:
        pending = await session.scalar(
            select(func.count()).select_from(Event).where(
                Event.status == EVENT_STATUS_PENDING
            )
        )
        completed = await session.scalar(
            select(func.count()).select_from(Event).where(
                Event.status == EVENT_STATUS_COMPLETED
            )
        )
        failed = await session.scalar(
            select(func.count()).select_from(Event).where(
                Event.status == EVENT_STATUS_FAILED
            )
        )
        dead = await session.scalar(
            select(func.count()).select_from(Event).where(
                Event.status == EVENT_STATUS_DEAD_LETTER
            )
        )
        avg_db = await session.scalar(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        Event.processed_at - Event.created_at,
                    )
                )
            ).where(
                Event.status == EVENT_STATUS_COMPLETED,
                Event.processed_at.is_not(None),
            )
        )

    return {
        "total_events": _metrics.total_events,
        "successful_events": _metrics.successful_events,
        "failed_events": _metrics.failed_events,
        "dead_letter_events": _metrics.dead_letter_events,
        "average_processing_time_ms": round(_metrics.average_processing_time, 2),
        "average_processing_time_seconds": round(
            _metrics.average_processing_time / 1000, 4
        ),
        "queue": {
            "pending": int(pending or 0),
            "completed": int(completed or 0),
            "failed": int(failed or 0),
            "dead_letter": int(dead or 0),
        },
        "db_average_processing_seconds": round(float(avg_db or 0), 4),
    }
