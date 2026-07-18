# Workflow KPI subscriber — cache invalidation on workflow lifecycle events.

from __future__ import annotations

import logging

from events.base_event import BaseEvent
from events.workflow_events import (
    WorkflowCancelledEvent,
    WorkflowCompletedEvent,
    WorkflowStartedEvent,
    WorkflowStepCompletedEvent,
)
from services.kpi_service import kpi_service

logger = logging.getLogger(__name__)

_subscribed = False


class WorkflowKpiService:
    @staticmethod
    async def handle_event(event: BaseEvent) -> None:
        if isinstance(
            event,
            (
                WorkflowStartedEvent,
                WorkflowStepCompletedEvent,
                WorkflowCompletedEvent,
                WorkflowCancelledEvent,
            ),
        ):
            kpi_service.invalidate_cache()

    @staticmethod
    def subscribe_to_event_bus() -> None:
        global _subscribed
        if _subscribed:
            return
        from events.event_bus import subscribe

        for event_type in (
            WorkflowStartedEvent,
            WorkflowStepCompletedEvent,
            WorkflowCompletedEvent,
            WorkflowCancelledEvent,
        ):
            subscribe(
                event_type,
                WorkflowKpiService.handle_event,
                handler_id=f"workflow_kpi_{event_type.__name__}",
            )
        _subscribed = True
        logger.info("workflow_kpi_subscribed")

    @staticmethod
    def reset_subscription() -> None:
        global _subscribed
        _subscribed = False


workflow_kpi_service = WorkflowKpiService()
