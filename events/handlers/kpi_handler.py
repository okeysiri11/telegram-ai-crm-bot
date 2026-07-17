# KPI side effects for platform request events.

from __future__ import annotations

from services.kpi_service import KpiService
from events.base_event import BaseEvent


class KpiEventHandler:
    @staticmethod
    async def handle(event: BaseEvent) -> None:
        await KpiService.handle_event(event)
