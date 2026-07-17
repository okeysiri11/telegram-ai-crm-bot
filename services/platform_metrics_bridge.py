# Platform metrics bridge — CRM event bus subscribers (async, non-blocking for handlers).

from __future__ import annotations

import logging
import uuid

from database.models.client_request import ClientRequestStatus, CrmFunnelStage

logger = logging.getLogger(__name__)

_handlers_registered = False


async def _on_request_created(event) -> None:
    from services.platform_metrics_service import PlatformMetricsService

    payload = event.payload or {}
    request_number = payload.get("request_number")
    if not request_number:
        return
    await PlatformMetricsService._write_request_created(
        request_number=str(request_number),
        request_type=str(payload.get("request_type") or "UNKNOWN"),
        status=str(payload.get("status") or ClientRequestStatus.NEW.value),
        vertical=payload.get("vertical"),
        request_id=event.aggregate_id,
        manager_id=payload.get("manager_id"),
        client_telegram_id=payload.get("client_telegram_id"),
    )


async def _on_request_assigned(event) -> None:
    from services.platform_metrics_service import PlatformMetricsService

    payload = event.payload or {}
    request_number = payload.get("request_number")
    manager_id = payload.get("manager_id")
    if not request_number or not manager_id:
        return
    await PlatformMetricsService._write_manager_assigned(
        request_number=str(request_number),
        manager_id=manager_id,
        status=ClientRequestStatus.ASSIGNED.value,
    )


async def _on_status_changed(event) -> None:
    from services.platform_metrics_service import PlatformMetricsService

    payload = event.payload or {}
    request_number = payload.get("request_number")
    status = str(payload.get("status") or "")
    if not request_number or not status:
        return

    if status == ClientRequestStatus.IN_PROGRESS.value:
        await PlatformMetricsService._write_manager_first_response(
            request_number=str(request_number),
            status=status,
            manager_id=payload.get("manager_id"),
        )
        return

    if status in {
        ClientRequestStatus.COMPLETED.value,
        ClientRequestStatus.CANCELLED.value,
    }:
        funnel = str(payload.get("funnel_stage") or "")
        is_deal = status == ClientRequestStatus.COMPLETED.value or funnel == CrmFunnelStage.DEAL.value
        await PlatformMetricsService._write_request_closed(
            request_number=str(request_number),
            status=status,
            converted_to_deal=is_deal,
        )


def register_platform_metrics_handlers() -> None:
    global _handlers_registered
    if _handlers_registered:
        return

    from services import crm_event_bus as event_bus

    event_bus.subscribe(
        "client_request.created",
        _on_request_created,
        handler_id="platform_metrics_created",
    )
    event_bus.subscribe(
        "client_request.assigned",
        _on_request_assigned,
        handler_id="platform_metrics_assigned",
    )
    event_bus.subscribe(
        "client_request.status_changed",
        _on_status_changed,
        handler_id="platform_metrics_status",
    )
    _handlers_registered = True
    logger.info("platform_metrics_event_handlers_registered")
