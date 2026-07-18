# Dashboard metrics — widget data for Operations Center.

from __future__ import annotations

from typing import Any

from platform_observability.anomaly_detector import anomaly_detector
from platform_observability.health_monitor import health_monitor
from platform_observability.metrics_service import metrics_service
from platform_observability.performance_monitor import performance_monitor


async def collect_and_analyze() -> None:
    await metrics_service.collect_platform_metrics()
    await anomaly_detector.analyze(metrics_service.summary())


async def platform_health_widget(_ctx=None) -> dict[str, Any]:
    health = await health_monitor.check_all()
    return {
        "overall_status": health["overall_status"],
        "components": {k: v.get("status") for k, v in health["components"].items()},
    }


async def performance_widget(_ctx=None) -> dict[str, Any]:
    await collect_and_analyze()
    return performance_monitor.summary()


async def slowest_apis_widget(_ctx=None) -> dict[str, Any]:
    return {"endpoints": performance_monitor.slowest_apis(limit=10)}


async def queue_health_widget(_ctx=None) -> dict[str, Any]:
    summary = metrics_service.summary()
    return {
        "jobs_queue_size": summary.get("jobs.queue.size", {}).get("last", 0),
        "jobs_dead_letter": summary.get("jobs.dead_letter.count", {}).get("last", 0),
    }


async def worker_health_widget(_ctx=None) -> dict[str, Any]:
    try:
        from platform_jobs.worker_manager import worker_manager

        return worker_manager.health_summary()
    except Exception:
        return {"status": "unknown"}


async def integration_health_widget(_ctx=None) -> dict[str, Any]:
    try:
        from platform_integrations.integration_service import integration_service

        return await integration_service.health()
    except Exception as exc:
        return {"overall_status": "unknown", "error": str(exc)}


async def realtime_health_widget(_ctx=None) -> dict[str, Any]:
    summary = metrics_service.summary()
    return {
        "connections": summary.get("realtime.connections.count", {}).get("last", 0),
        "messages_per_second": summary.get("realtime.messages_per_second", {}).get("last", 0),
    }


async def database_health_widget(_ctx=None) -> dict[str, Any]:
    health = await health_monitor.check_all()
    return health["components"].get("database", {"status": "unknown"})


async def all_dashboard_widgets() -> dict[str, Any]:
    await collect_and_analyze()
    return {
        "platform_health": await platform_health_widget(),
        "performance": await performance_widget(),
        "slowest_apis": await slowest_apis_widget(),
        "queue_health": await queue_health_widget(),
        "worker_health": await worker_health_widget(),
        "integration_health": await integration_health_widget(),
        "realtime_health": await realtime_health_widget(),
        "database_health": await database_health_widget(),
    }


async def status_snapshot() -> dict[str, Any]:
    await collect_and_analyze()
    from platform_observability.alert_manager import alert_manager
    from platform_observability.logging_service import logging_service
    from platform_observability.retention_manager import retention_manager
    from platform_observability.tracing_service import tracing_service

    health = await health_monitor.check_all()
    return {
        "health": health,
        "metrics_catalog": metrics_service.catalog(),
        "metrics_summary": metrics_service.summary(),
        "performance": performance_monitor.summary(),
        "alerts": [a.to_dict() for a in alert_manager.list_alerts()],
        "anomalies": anomaly_detector.recent_anomalies(),
        "retention": retention_manager.get_policy().to_dict(),
        "log_count": len(logging_service._entries),
        "trace_count": len(tracing_service._spans),
    }
