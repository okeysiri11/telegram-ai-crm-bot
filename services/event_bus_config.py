# Event bus worker configuration — sourced from ConfigurationCenter.

from __future__ import annotations

from platform_configuration.configuration_center import configuration_center
from platform_configuration.event_bus_policy import (
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
    compute_backoff_seconds,
)

__all__ = [
    "MAX_RETRIES",
    "RETRY_DELAY_SECONDS",
    "compute_backoff_seconds",
    "HANDLER_TIMEOUT_SECONDS",
    "DEFAULT_WORKER_COUNT",
    "POLL_INTERVAL_SECONDS",
]


def _eb():
    return configuration_center.settings.event_bus


HANDLER_TIMEOUT_SECONDS: float = _eb().handler_timeout_seconds
DEFAULT_WORKER_COUNT: int = _eb().worker_count
POLL_INTERVAL_SECONDS: float = _eb().poll_interval_seconds
