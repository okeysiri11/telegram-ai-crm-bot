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
    "email_send_attempt_total": 0,
    "email_send_success_total": 0,
    "email_send_failure_total": 0,
    "email_retry_total": 0,
    "email_rate_limited_total": 0,
    "email_provider_health": 0,
    "email_send_latency": 0,
    "whatsapp_send_attempt_total": 0,
    "whatsapp_send_success_total": 0,
    "whatsapp_send_failure_total": 0,
    "whatsapp_webhook_received_total": 0,
    "whatsapp_webhook_duplicate_total": 0,
    "whatsapp_message_delivered_total": 0,
    "whatsapp_message_read_total": 0,
    "whatsapp_provider_health": 0,
    "whatsapp_rate_limited_total": 0,
    "whatsapp_send_latency": 0,
}

_METRIC_META: dict[str, tuple[str, str]] = {
    "http_requests_total": ("counter", "Total HTTP requests"),
    "leads_created_total": ("counter", "Total leads created"),
    "notifications_sent_total": ("counter", "Total notifications sent"),
    "sla_violations_total": ("counter", "Total SLA violations"),
    "process_start_time": ("gauge", "Process start unix time"),
    "email_send_attempt_total": ("counter", "Recruiting SMTP send attempts"),
    "email_send_success_total": ("counter", "Recruiting SMTP accepted sends"),
    "email_send_failure_total": ("counter", "Recruiting SMTP send failures"),
    "email_retry_total": ("counter", "Recruiting SMTP retries"),
    "email_rate_limited_total": ("counter", "Recruiting SMTP rate-limit hits"),
    "email_provider_health": ("gauge", "Recruiting SMTP health 1=up 0=not configured -1=error"),
    "email_send_latency": ("gauge", "Last Recruiting SMTP send latency milliseconds"),
    "whatsapp_send_attempt_total": ("counter", "Recruiting WhatsApp send attempts"),
    "whatsapp_send_success_total": ("counter", "Recruiting WhatsApp accepted sends"),
    "whatsapp_send_failure_total": ("counter", "Recruiting WhatsApp send failures"),
    "whatsapp_webhook_received_total": ("counter", "Recruiting WhatsApp webhooks received"),
    "whatsapp_webhook_duplicate_total": ("counter", "Recruiting WhatsApp duplicate webhooks"),
    "whatsapp_message_delivered_total": ("counter", "Recruiting WhatsApp delivered receipts"),
    "whatsapp_message_read_total": ("counter", "Recruiting WhatsApp read receipts"),
    "whatsapp_provider_health": ("gauge", "Recruiting WhatsApp health 1=up 0=not configured -1=error"),
    "whatsapp_rate_limited_total": ("counter", "Recruiting WhatsApp rate-limit hits"),
    "whatsapp_send_latency": ("gauge", "Last Recruiting WhatsApp send latency milliseconds"),
}


def configure_structured_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def init_sentry() -> bool:
    from services.error_tracking_service import ErrorTrackingService

    return ErrorTrackingService.ensure_sentry()


def inc_metric(name: str, value: float = 1.0) -> None:
    _METRICS[name] = _METRICS.get(name, 0) + value


def set_metric(name: str, value: float) -> None:
    _METRICS[name] = float(value)


def prometheus_text() -> str:
    lines: list[str] = []
    for name, value in _METRICS.items():
        kind, help_text = _METRIC_META.get(name, ("gauge", name.replace("_", " ")))
        prom_name = "process_start_time_seconds" if name == "process_start_time" else name
        lines.append(f"# HELP {prom_name} {help_text}")
        lines.append(f"# TYPE {prom_name} {kind}")
        lines.append(f"{prom_name} {value}")
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
