# Observability Engine v1 — operational monitoring, KPIs, latency, and error tracking.

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, AsyncIterator

from config import OWNER_ID
from database.models.observability_engine import ErrorSeverity
from database.session import get_session
from repositories.observability_engine_repository import (
    BusinessMetricRepository,
    ErrorEventRepository,
    PerformanceMetricRepository,
    SystemMetricRepository,
)
from repositories.user_role_repository import UserRoleRepository

logger = logging.getLogger(__name__)

OBSERVABILITY_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})

DEFAULT_BUSINESS_KPIS = (
    "deals.active_count",
    "deals.closed_today",
    "vehicles.in_stock",
    "vehicles.sold_today",
    "payments.completed_today",
    "settlements.completed_today",
)


class ObservabilityEngineError(Exception):
    pass


class ObservabilityEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in OBSERVABILITY_ROLES for role in roles)

    @staticmethod
    async def record_system_metric(
        *,
        metric_name: str,
        metric_value: Decimal | float | int,
        unit: str = "count",
        tags: dict | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        async with get_session() as session:
            row = await SystemMetricRepository(session).record(
                metric_name=metric_name,
                metric_value=metric_value,
                unit=unit,
                tags=tags,
                recorded_at=now,
            )
            return {
                "id": str(row.id),
                "metric_name": row.metric_name,
                "metric_value": float(row.metric_value),
                "unit": row.unit,
                "recorded_at": row.recorded_at.isoformat(),
            }

    @staticmethod
    async def record_business_metric(
        *,
        kpi_name: str,
        kpi_value: Decimal | float | int,
        unit: str = "count",
        dimensions: dict | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        async with get_session() as session:
            row = await BusinessMetricRepository(session).record(
                kpi_name=kpi_name,
                kpi_value=kpi_value,
                unit=unit,
                dimensions=dimensions,
                period_start=period_start,
                period_end=period_end,
                recorded_at=now,
            )
            return {
                "id": str(row.id),
                "kpi_name": row.kpi_name,
                "kpi_value": float(row.kpi_value),
                "unit": row.unit,
                "recorded_at": row.recorded_at.isoformat(),
            }

    @staticmethod
    async def record_error_event(
        *,
        source: str,
        error_type: str,
        message: str,
        stack_trace: str | None = None,
        context: dict | None = None,
        severity: str = ErrorSeverity.ERROR.value,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        async with get_session() as session:
            row = await ErrorEventRepository(session).record(
                source=source,
                error_type=error_type,
                message=message,
                stack_trace=stack_trace,
                context=context,
                severity=severity,
                recorded_at=now,
            )
            return {
                "id": str(row.id),
                "source": row.source,
                "error_type": row.error_type,
                "severity": row.severity,
                "recorded_at": row.recorded_at.isoformat(),
            }

    @staticmethod
    async def record_performance(
        *,
        operation_name: str,
        latency_ms: Decimal | float | int,
        success: bool = True,
        tags: dict | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        async with get_session() as session:
            row = await PerformanceMetricRepository(session).record(
                operation_name=operation_name,
                latency_ms=latency_ms,
                success=success,
                tags=tags,
                recorded_at=now,
            )
            return {
                "id": str(row.id),
                "operation_name": row.operation_name,
                "latency_ms": float(row.latency_ms),
                "success": row.success,
                "recorded_at": row.recorded_at.isoformat(),
            }

    @staticmethod
    @asynccontextmanager
    async def track_latency(
        operation_name: str,
        *,
        tags: dict | None = None,
    ) -> AsyncIterator[None]:
        started = time.perf_counter()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            try:
                await ObservabilityEngineV1.record_performance(
                    operation_name=operation_name,
                    latency_ms=elapsed_ms,
                    success=success,
                    tags=tags,
                )
            except Exception:
                logger.exception("observability_latency_record_failed")

    @staticmethod
    async def collect_platform_snapshot() -> dict[str, Any]:
        """Collect queue depth, throughput, and system health from platform engines."""
        from services import crm_event_bus as event_bus
        from services import event_bus_metrics

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=1)

        queue_size = await event_bus.get_queue_size()
        bus_metrics = await event_bus_metrics.get_metrics()

        async with get_session() as session:
            sys_repo = SystemMetricRepository(session)
            for name, value in (
                ("event_bus.queue.pending", queue_size.get("pending", 0)),
                ("event_bus.queue.failed", queue_size.get("failed", 0)),
                ("event_bus.queue.dead_letter", queue_size.get("dead_letter", 0)),
                ("event_bus.throughput.total", bus_metrics.get("total_events", 0)),
                ("event_bus.throughput.success", bus_metrics.get("successful_events", 0)),
                ("event_bus.throughput.failed", bus_metrics.get("failed_events", 0)),
            ):
                await sys_repo.record(
                    metric_name=name,
                    metric_value=value,
                    unit="count",
                    recorded_at=now,
                )

            try:
                from repositories.webhook_engine_repository import (
                    WebhookDeliveryRepository,
                )

                pending_webhooks = len(
                    await WebhookDeliveryRepository(session).list_dead_letter(limit=1000)
                )
                await sys_repo.record(
                    metric_name="webhook.queue.dead_letter",
                    metric_value=pending_webhooks,
                    unit="count",
                    recorded_at=now,
                )
            except Exception:
                pass

            try:
                from repositories.scheduler_engine_repository import (
                    ScheduledJobRepository,
                )

                due_jobs = await ScheduledJobRepository(session).list_active()
                await sys_repo.record(
                    metric_name="scheduler.jobs.active",
                    metric_value=len(due_jobs),
                    unit="count",
                    recorded_at=now,
                )
            except Exception:
                pass

            await session.commit()

        return {
            "collected_at": now.isoformat(),
            "queue_depth": queue_size,
            "event_throughput": {
                "total": bus_metrics.get("total_events", 0),
                "successful": bus_metrics.get("successful_events", 0),
                "failed": bus_metrics.get("failed_events", 0),
                "dead_letter": bus_metrics.get("dead_letter_events", 0),
                "avg_processing_ms": bus_metrics.get("average_processing_time_ms", 0),
            },
            "window_start": window_start.isoformat(),
        }

    @staticmethod
    async def collect_business_kpis(*, actor_id: int = OWNER_ID) -> dict[str, Any]:
        """Snapshot key business KPIs from domain engines."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        kpis: dict[str, float] = {}

        try:
            from sqlalchemy import func, select

            from database.models.deal import TERMINAL_DEAL_STATUSES, Deal, DealStatus

            async with get_session() as session:
                active_count = await session.scalar(
                    select(func.count())
                    .select_from(Deal)
                    .where(Deal.status.not_in(TERMINAL_DEAL_STATUSES))
                )
                closed_today = await session.scalar(
                    select(func.count())
                    .select_from(Deal)
                    .where(
                        Deal.status == DealStatus.COMPLETED.value,
                        Deal.updated_at >= today_start,
                    )
                )
                kpis["deals.active_count"] = int(active_count or 0)
                kpis["deals.closed_today"] = int(closed_today or 0)
        except Exception:
            kpis["deals.active_count"] = 0
            kpis["deals.closed_today"] = 0

        try:
            from repositories.automotive_inventory_repository import VehicleRepository

            async with get_session() as session:
                vehicles = await VehicleRepository(session).list_all(limit=10000)
                kpis["vehicles.in_stock"] = sum(
                    1 for v in vehicles if getattr(v, "status", "") in {"IN_STOCK", "LISTED", "RESERVED"}
                )
                kpis["vehicles.sold_today"] = sum(
                    1
                    for v in vehicles
                    if getattr(v, "status", "") == "SOLD"
                    and getattr(v, "updated_at", now) >= today_start
                )
        except Exception:
            kpis["vehicles.in_stock"] = 0
            kpis["vehicles.sold_today"] = 0

        async with get_session() as session:
            biz_repo = BusinessMetricRepository(session)
            for name, value in kpis.items():
                await biz_repo.record(
                    kpi_name=name,
                    kpi_value=value,
                    unit="count",
                    period_start=today_start,
                    period_end=now,
                    recorded_at=now,
                )
            await session.commit()

        return {"collected_at": now.isoformat(), "kpis": kpis}

    @staticmethod
    async def get_dashboard(
        *,
        actor_id: int,
        window_hours: int = 24,
    ) -> dict[str, Any]:
        if not await ObservabilityEngineV1.user_can_access(actor_id):
            raise ObservabilityEngineError("Access denied")

        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=window_hours)

        async with get_session() as session:
            sys_repo = SystemMetricRepository(session)
            perf_repo = PerformanceMetricRepository(session)
            err_repo = ErrorEventRepository(session)
            biz_repo = BusinessMetricRepository(session)

            queue_pending = await sys_repo.aggregate(
                metric_name="event_bus.queue.pending",
                since=since,
            )
            throughput = await sys_repo.aggregate(
                metric_name="event_bus.throughput.total",
                since=since,
            )
            event_handler_latency = await perf_repo.aggregate_latency(
                operation_name="event_bus.handler",
                since=since,
            )
            api_latency = await perf_repo.aggregate_latency(
                operation_name="api.request",
                since=since,
            )
            error_count = await err_repo.count_since(since=since)
            errors_by_source: dict[str, int] = {}
            for source in ("event_bus", "webhook", "scheduler", "api"):
                errors_by_source[source] = await err_repo.count_since(
                    since=since,
                    source=source,
                )
            latest_kpis = await biz_repo.latest_by_kpi(list(DEFAULT_BUSINESS_KPIS))
            recent_errors = await err_repo.list_recent(since=since, limit=20)

        return {
            "window_hours": window_hours,
            "generated_at": now.isoformat(),
            "queue_depth": {
                "event_bus_pending_avg": queue_pending["avg"],
                "event_bus_pending_max": queue_pending["max"],
            },
            "event_throughput": {
                "samples": throughput["count"],
                "avg_per_sample": throughput["avg"],
            },
            "latency": {
                "event_bus_handler": event_handler_latency,
                "api_request": api_latency,
            },
            "error_rates": {
                "total_errors": error_count,
                "by_source": errors_by_source,
            },
            "business_kpis": {
                name: {
                    "value": float(row.kpi_value),
                    "unit": row.unit,
                    "recorded_at": row.recorded_at.isoformat(),
                }
                for name, row in latest_kpis.items()
            },
            "recent_errors": [
                {
                    "id": str(err.id),
                    "source": err.source,
                    "error_type": err.error_type,
                    "message": err.message[:200],
                    "severity": err.severity,
                    "recorded_at": err.recorded_at.isoformat(),
                }
                for err in recent_errors
            ],
        }
