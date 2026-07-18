# Legacy adapters — sole gateway to handlers, database_legacy, services/pg_*, openrouter.

from __future__ import annotations

import inspect
import logging
import time
from typing import Any, Callable

from platform_legacy.interfaces import (
    LegacyAI,
    LegacyAnalytics,
    LegacyAudit,
    LegacyCRM,
    LegacyNotificationGateway,
    LegacyScheduler,
    LegacyTelegram,
    LegacyUserStorage,
    LegacyWorkflowRules,
)
from platform_legacy.models import LegacyCallRecord

logger = logging.getLogger(__name__)


def _caller_frame(skip: int = 2) -> str:
    frame = inspect.currentframe()
    for _ in range(skip):
        if frame is None:
            return "unknown"
        frame = frame.f_back
    if frame is None:
        return "unknown"
    module = frame.f_globals.get("__name__", "unknown")
    func = frame.f_code.co_name
    return f"{module}.{func}"


class TracedAdapter:
    """Base adapter — logs every legacy call with latency and success."""

    adapter_name: str = "base"

    def __init__(self, *, registry: Any | None = None) -> None:
        self._registry = registry

    def _record(
        self,
        method: str,
        *,
        success: bool,
        latency_ms: float,
        caller: str,
        error: str | None = None,
    ) -> None:
        record = LegacyCallRecord(
            adapter=self.adapter_name,
            method=method,
            caller=caller,
            success=success,
            latency_ms=latency_ms,
            error=error,
        )
        logger.info(
            "legacy_call adapter=%s method=%s caller=%s latency_ms=%.2f success=%s",
            record.adapter,
            record.method,
            record.caller,
            record.latency_ms,
            record.success,
            extra={
                "legacy_adapter": record.adapter,
                "legacy_method": record.method,
                "legacy_caller": record.caller,
                "legacy_latency_ms": record.latency_ms,
                "legacy_success": record.success,
            },
        )
        if self._registry is not None:
            self._registry.record_call(record)

    def _trace(self, method: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        caller = _caller_frame(3)
        started = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
            if inspect.isawaitable(result):
                return self._trace_async(method, caller, started, result)
            latency = (time.perf_counter() - started) * 1000
            self._record(method, success=True, latency_ms=latency, caller=caller)
            return result
        except Exception as exc:
            latency = (time.perf_counter() - started) * 1000
            self._record(
                method,
                success=False,
                latency_ms=latency,
                caller=caller,
                error=str(exc),
            )
            raise

    async def _trace_async(
        self,
        method: str,
        caller: str,
        started: float,
        coro: Any,
    ) -> Any:
        try:
            result = await coro
            latency = (time.perf_counter() - started) * 1000
            self._record(method, success=True, latency_ms=latency, caller=caller)
            return result
        except Exception as exc:
            latency = (time.perf_counter() - started) * 1000
            self._record(
                method,
                success=False,
                latency_ms=latency,
                caller=caller,
                error=str(exc),
            )
            raise


class CRMAdapter(TracedAdapter, LegacyCRM):
    adapter_name = "crm"

    async def submit_auto_request(self, **kwargs: Any) -> dict[str, Any]:
        from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

        return await self._trace(
            "submit_auto_request",
            AutoClientRequestEngineV1.submit,
            **kwargs,
        )

    async def get_auto_request_summary(self, request_number: str) -> dict[str, Any] | None:
        from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

        return await self._trace(
            "get_auto_request_summary",
            AutoClientRequestEngineV1.get_request_summary,
            request_number,
        )

    async def list_new_auto_requests(self, *, limit: int = 10) -> list[dict[str, Any]]:
        from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

        return await self._trace(
            "list_new_auto_requests",
            AutoClientRequestEngineV1.list_new_request_summaries,
            limit=limit,
        )

    async def ingest_lead_from_deep_link(self, **kwargs: Any) -> dict[str, Any]:
        from services.pg_lead_engine import LeadEngineV1

        return await self._trace(
            "ingest_lead_from_deep_link",
            LeadEngineV1.ingest_from_deep_link,
            **kwargs,
        )

    async def record_vin_intake(self, *, vin: str, car_id: Any, created_by: int) -> None:
        from services.pg_vin_engine import VinEngineV1

        await self._trace(
            "record_vin_intake",
            VinEngineV1.record_car_intake,
            vin=vin,
            car_id=car_id,
            created_by=created_by,
        )

    async def get_default_tenant_id(self) -> Any:
        from services.pg_partner_tenant_engine import PartnerTenantEngineV1

        return await self._trace(
            "get_default_tenant_id",
            PartnerTenantEngineV1.get_default_tenant_id,
        )


class TelegramAdapter(TracedAdapter, LegacyTelegram):
    adapter_name = "telegram"

    def register_bot_routers(self, dispatcher: Any) -> None:
        def _register() -> None:
            from auto_vertical_handlers import auto_vertical_router as auto_router
            from handlers import router
            from routers.auto_client_router import router as auto_client_entry_router
            from routers.auto_dealer_router import router as auto_dealer_entry_router
            from routers.auto_hub_router import router as auto_hub_router
            from routers.client_history_router import router as client_history_router
            from routers.manager_crm_router import router as manager_crm_router
            from routers.manager_dashboard_router import router as manager_dashboard_router
            from routers.manager_debug_router import router as manager_debug_router
            from routers.realty_router import router as realty_router

            dispatcher.include_router(auto_client_entry_router)
            dispatcher.include_router(auto_dealer_entry_router)
            dispatcher.include_router(client_history_router)
            dispatcher.include_router(manager_crm_router)
            dispatcher.include_router(manager_dashboard_router)
            dispatcher.include_router(manager_debug_router)
            dispatcher.include_router(auto_hub_router)
            dispatcher.include_router(realty_router)
            dispatcher.include_router(auto_router)
            dispatcher.include_router(router)

        self._trace("register_bot_routers", _register)


class PermissionsAdapter(TracedAdapter, LegacyUserStorage):
    adapter_name = "permissions"

    async def user_has_permission(self, telegram_id: int, permission_code: str) -> bool:
        from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1

        return await self._trace(
            "user_has_permission",
            PlatformPermissionsEngineV1.user_has_permission,
            telegram_id,
            permission_code,
        )

    async def ensure_permissions_seeded(self) -> dict[str, Any]:
        from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1

        return await self._trace(
            "ensure_permissions_seeded",
            PlatformPermissionsEngineV1.ensure_seeded,
        )


class NotificationAdapter(TracedAdapter, LegacyNotificationGateway):
    adapter_name = "notification"

    async def send_to_manager(
        self,
        *,
        manager_telegram_id: int,
        text: str,
        request_number: str | None = None,
    ) -> None:
        from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

        await self._trace(
            "send_to_manager",
            ManagerDeliveryEngineV1.send_to_manager,
            manager_telegram_id=int(manager_telegram_id),
            text=text,
            request_number=request_number,
        )

    async def startup_diagnostics(self) -> dict[str, Any]:
        from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

        return await self._trace(
            "startup_diagnostics",
            ManagerDeliveryEngineV1.startup_diagnostics,
        )


class AuditAdapter(TracedAdapter, LegacyAudit):
    adapter_name = "audit"

    async def log(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        user_id: int | None,
        payload: dict[str, Any],
    ) -> str | None:
        from services.pg_platform_audit_engine import PlatformAuditEngineV1

        return await self._trace(
            "log",
            PlatformAuditEngineV1.log,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
        )


class SchedulerAdapter(TracedAdapter, LegacyScheduler):
    adapter_name = "scheduler"

    def get_default_worker(self) -> Any:
        from services.pg_scheduler_engine import get_default_worker

        return self._trace("get_default_worker", get_default_worker)


class AIAdapter(TracedAdapter, LegacyAI):
    adapter_name = "ai"

    async def ask(self, prompt: str, **kwargs: Any) -> str:
        from openrouter import ask_openrouter

        return await self._trace("ask", ask_openrouter, prompt, **kwargs)


class AnalyticsAdapter(TracedAdapter, LegacyAnalytics):
    adapter_name = "analytics"

    async def owner_dashboard_metrics(self) -> dict[str, Any]:
        from services.pg_owner_analytics_engine import OwnerAnalyticsEngineV1

        return await self._trace(
            "owner_dashboard_metrics",
            OwnerAnalyticsEngineV1.get_dashboard_metrics,
        )


class WorkflowRulesAdapter(TracedAdapter, LegacyWorkflowRules):
    adapter_name = "workflow_rules"

    def register_trigger(
        self,
        trigger_code: str,
        action_type: str,
        module: str = "system",
        action_payload: str | None = None,
    ) -> int:
        from database import register_workflow_rule

        return self._trace(
            "register_trigger",
            register_workflow_rule,
            trigger_code,
            action_type,
            module,
            action_payload,
        )

    def fetch_rules(self, trigger_code: str) -> list[tuple[Any, ...]]:
        from database import get_workflow_rules

        return self._trace("fetch_rules", get_workflow_rules, trigger_code=trigger_code)

    def log_execution(
        self,
        trigger_code: str,
        user_id: int,
        module: str,
        action_type: str,
        *,
        entity_type: str | None = None,
        entity_id: int | None = None,
        status: str = "OK",
        details: str | None = None,
    ) -> int:
        from database import log_workflow_execution

        return self._trace(
            "log_execution",
            log_workflow_execution,
            trigger_code,
            user_id,
            module,
            action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            details=details,
        )


class SlaAdapter(TracedAdapter):
    adapter_name = "sla"

    async def on_lead_created(self, **kwargs: Any) -> None:
        from services.pg_lead_sla_engine import LeadSlaEngineV1

        await self._trace("on_lead_created", LeadSlaEngineV1.on_lead_created, **kwargs)

    async def on_assigned(self, **kwargs: Any) -> None:
        from services.pg_lead_sla_engine import LeadSlaEngineV1

        await self._trace("on_assigned", LeadSlaEngineV1.on_assigned, **kwargs)

    async def on_closed(self, **kwargs: Any) -> None:
        from services.pg_lead_sla_engine import LeadSlaEngineV1

        await self._trace("on_closed", LeadSlaEngineV1.on_closed, **kwargs)

    async def raise_priority(self, **kwargs: Any) -> None:
        from services.pg_lead_sla_engine import LeadSlaEngineV1

        await self._trace("raise_priority", LeadSlaEngineV1.raise_priority, **kwargs)


class BootstrapAdapter(TracedAdapter):
    """Startup-only legacy wiring (scheduler, webhooks, routing seeds)."""

    adapter_name = "bootstrap"

    def configure_bidex_parser(self) -> None:
        from services.bidex_telegram_quote_parser import configure_bidex_parser
        from services.pg_dealer_quote_authority_engine import DealerQuoteAuthorityEngineV1

        self._trace(
            "configure_bidex_parser",
            configure_bidex_parser,
            DealerQuoteAuthorityEngineV1,
        )

    def register_webhook_handlers(self) -> None:
        from services.pg_webhook_engine import WebhookEngineV1

        self._trace("register_webhook_handlers", WebhookEngineV1.register_event_handlers)

    async def ensure_vertical_routing(self) -> dict[str, Any]:
        from services.pg_vertical_routing_engine import VerticalRoutingEngineV1

        return await self._trace(
            "ensure_vertical_routing",
            VerticalRoutingEngineV1.ensure_platform_actors,
        )


class LegacyEventsAdapter(TracedAdapter):
    """Bridge to platform_events_legacy SQLite bus."""

    adapter_name = "events"

    def legacy_event_bus_class(self) -> Any:
        from platform_events_legacy import EventBus

        return EventBus

    def legacy_platform_event_class(self) -> Any:
        from platform_events_legacy import PlatformEvent

        return PlatformEvent

    def reset_event_bus_for_tests(self) -> None:
        from platform_events_legacy import reset_event_bus_for_tests

        reset_event_bus_for_tests()
