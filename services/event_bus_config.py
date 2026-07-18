# Event bus worker configuration — sourced from ConfigurationCenter.

from __future__ import annotations

from platform_configuration.configuration_center import configuration_center


def _eb():
    return configuration_center.settings.event_bus


MAX_RETRIES: int = _eb().max_retries
RETRY_DELAY_SECONDS: float = _eb().retry_delay_seconds
HANDLER_TIMEOUT_SECONDS: float = _eb().handler_timeout_seconds
DEFAULT_WORKER_COUNT: int = _eb().worker_count
POLL_INTERVAL_SECONDS: float = _eb().poll_interval_seconds
