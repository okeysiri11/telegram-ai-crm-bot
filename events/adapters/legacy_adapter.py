# Legacy EventBus adapter — all legacy events pass through PlatformEventBus.

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Callable

from events.event_bus import PlatformEventBus
from events.generic_events import GenericPlatformEvent
from platform_legacy import legacy

PlatformEvent = legacy.events.legacy_platform_event_class()

logger = logging.getLogger(__name__)

_legacy_bridge_registered = False


async def publish_legacy_to_platform_bus(
    event: PlatformEvent,
    *,
    wait: bool = False,
) -> dict[str, Any]:
    """Publish a legacy PlatformEvent through the canonical PlatformEventBus."""
    generic = GenericPlatformEvent.from_legacy(
        event_type=event.event_type,
        user_id=event.user_id,
        module=event.module,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        payload=event.payload,
        legacy_event_id=event.event_id,
    )
    return await PlatformEventBus.publish(generic, wait=wait)


def publish_legacy_to_platform_bus_sync(
    event: PlatformEvent,
    *,
    wait: bool = False,
) -> dict[str, Any]:
    """Sync wrapper for legacy callers."""
    import asyncio

    coro = publish_legacy_to_platform_bus(event, wait=wait)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    if wait:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    asyncio.get_running_loop().create_task(coro)
    return {"event_type": event.event_type, "handlers": 0, "errors": [], "scheduled": True}


def _to_platform_event(event: GenericPlatformEvent) -> PlatformEvent:
    return PlatformEvent(
        event_type=event.name,
        module=event.module or "",
        entity_type=event.entity_type or "",
        entity_id=event.entity_id,
        user_id=event.user_id or 0,
        payload=dict(event.payload),
        created_at=event.occurred_at.strftime("%Y-%m-%d %H:%M:%S"),
        status="PUBLISHED",
        event_id=event.payload.get("legacy_event_id"),
    )


def _wrap_legacy_handler(handler: Callable[[PlatformEvent], Any], handler_id: str) -> Callable:
    async def _async_wrapper(event: GenericPlatformEvent) -> None:
        platform_event = _to_platform_event(event)
        try:
            result = handler(platform_event)
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.exception(
                "legacy_handler_failed",
                extra={"handler_id": handler_id, "event_type": event.name},
            )
            raise

    return _async_wrapper


def register_legacy_handlers_on_platform_bus() -> int:
    """Wire event_bus_bridge handlers to PlatformEventBus (idempotent)."""
    global _legacy_bridge_registered
    if _legacy_bridge_registered:
        return 0

    import importlib.util
    from pathlib import Path

    bridge_path = Path(__file__).resolve().parents[2] / "services" / "event_bus_bridge.py"
    spec = importlib.util.spec_from_file_location("event_bus_bridge", bridge_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("event_bus_bridge module not found")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    handlers = [
        ("AGRO_REQUEST_CREATED", mod._on_agro_request_created, "agro_lifecycle"),
        ("AGRO_REQUEST_CREATED", mod._on_agro_request_workflow, "agro_workflow_engine"),
        ("AGRO_REQUEST_CREATED", mod._on_agro_request_notify, "agro_notify"),
        ("AGRO_REQUEST_CREATED", mod._on_agro_erp_request_created, "agro_erp_workflow"),
        ("AGRO_REQUEST_ASSIGNED", mod._on_agro_request_assigned, "agro_assigned"),
        ("AGRO_REQUEST_ASSIGNED", mod._on_agro_erp_taken, "agro_erp_taken"),
        ("AGRO_REQUEST_STATUS_CHANGED", mod._on_agro_status_changed, "agro_status"),
        ("FINANCE_PAYMENT_CONFIRMED", mod._on_finance_payment_confirmed, "finance_audit"),
        ("FINANCE_COMMISSION_PAID", mod._on_finance_commission_paid, "finance_commission"),
        ("TASK_CREATED", mod._on_task_created, "task_workflow"),
        ("CALENDAR_EVENT_CREATED", mod._on_calendar_event_created, "calendar_workflow"),
        ("USER_CREATED", mod._on_user_created, "user_workflow"),
        ("AUTO_LEAD_CREATED", mod._on_auto_lead_created, "auto_stub"),
        ("AUTO_PAYMENT_RECEIVED", mod._on_auto_payment_received, "auto_payment_stub"),
        ("AUTO_TRADEIN_STARTED", mod._on_auto_tradein_started, "auto_tradein_stub"),
        ("LEGAL_CASE_CREATED", mod._on_legal_case_created, "legal_stub"),
        ("DRONE_PROJECT_CREATED", mod._on_drone_project_created, "drone_stub"),
        ("DEAL_CREATED", mod._on_deal_created, "deal_workflow"),
        ("DEAL_STATUS_CHANGED", mod._on_deal_status_changed, "deal_workflow"),
        ("DEAL_COMPLETED", mod._on_deal_completed, "deal_workflow"),
        ("DEAL_COMPLETED", mod._on_deal_completed_commissions, "commission_accrual"),
        ("DEAL_COMPLETED", mod._on_deal_completed_partner_kpi, "partner_kpi"),
        ("PARTNER_ASSIGNED", mod._on_partner_assigned, "partner_workflow"),
        ("PARTNER_CREATED", mod._on_partner_created, "partner_workflow"),
        ("DEAL_COMPLETED", mod._on_deal_completed_ledger, "ledger_income"),
        ("LEDGER_ENTRY_CREATED", mod._on_ledger_entry_created, "ledger_workflow"),
        ("FINANCE_PAYMENT_CONFIRMED", mod._on_finance_payment_ledger_sync, "ledger_sync"),
        ("FINANCE_COMMISSION_PAID", mod._on_finance_commission_ledger_sync, "ledger_sync"),
    ]

    count = 0
    for event_type, handler, handler_id in handlers:
        PlatformEventBus.subscribe(
            event_type,
            _wrap_legacy_handler(handler, handler_id),
            handler_id=f"legacy_{handler_id}",
        )
        count += 1

    _legacy_bridge_registered = True
    logger.info("legacy_handlers_registered_on_platform_bus count=%s", count)
    return count


def reset_legacy_bridge_registration() -> None:
    global _legacy_bridge_registered
    _legacy_bridge_registered = False
