# Event bus retry policy — shared by repository and service layers.

from __future__ import annotations

from platform_configuration.configuration_center import configuration_center


def _settings():
    return configuration_center.settings.event_bus


MAX_RETRIES: int = _settings().max_retries
RETRY_DELAY_SECONDS: float = _settings().retry_delay_seconds


def compute_backoff_seconds(attempts: int) -> float:
    """Exponential backoff from configured base delay."""
    return RETRY_DELAY_SECONDS * (2 ** max(int(attempts) - 1, 0))
