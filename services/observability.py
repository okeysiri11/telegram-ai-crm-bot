# Observability — structured logging, Prometheus metrics, Sentry hook.

from __future__ import annotations

import logging
import time
from typing import Any

from aiohttp import web

logger = logging.getLogger(__name__)

_METRICS: dict[str, float] = {
    "http_requests_total": 0,
    "leads_created_total": 0,
    "notifications_sent_total": 0,
    "sla_violations_total": 0,
    "process_start_time": time.time(),
}


def configure_structured_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def init_sentry() -> bool:
    from config import SENTRY_DSN

    if not SENTRY_DSN:
        return False
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)
        logger.info("Sentry initialized")
        return True
    except Exception:
        logger.warning("Sentry init failed", exc_info=True)
        return False


def inc_metric(name: str, value: float = 1.0) -> None:
    _METRICS[name] = _METRICS.get(name, 0) + value


def prometheus_text() -> str:
    lines = [
        "# HELP http_requests_total Total HTTP requests",
        "# TYPE http_requests_total counter",
        f"http_requests_total {_METRICS.get('http_requests_total', 0)}",
        "# HELP leads_created_total Total leads created",
        "# TYPE leads_created_total counter",
        f"leads_created_total {_METRICS.get('leads_created_total', 0)}",
        "# HELP notifications_sent_total Total notifications sent",
        "# TYPE notifications_sent_total counter",
        f"notifications_sent_total {_METRICS.get('notifications_sent_total', 0)}",
        "# HELP sla_violations_total Total SLA violations",
        "# TYPE sla_violations_total counter",
        f"sla_violations_total {_METRICS.get('sla_violations_total', 0)}",
        "# HELP process_start_time_seconds Process start unix time",
        "# TYPE process_start_time_seconds gauge",
        f"process_start_time_seconds {_METRICS.get('process_start_time', 0)}",
    ]
    return "\n".join(lines) + "\n"


async def metrics_handler(request: web.Request) -> web.Response:
    from config import PROMETHEUS_ENABLED

    if not PROMETHEUS_ENABLED:
        return web.Response(text="Prometheus disabled", status=404)
    return web.Response(text=prometheus_text(), content_type="text/plain; version=0.0.4")


@web.middleware
async def prometheus_middleware(request: web.Request, handler):
    inc_metric("http_requests_total")
    return await handler(request)


def observability_snapshot() -> dict[str, Any]:
    return dict(_METRICS)
