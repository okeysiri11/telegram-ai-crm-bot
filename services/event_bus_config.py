# Event Bus production configuration.

from __future__ import annotations

import os

MAX_RETRIES: int = int(os.getenv("EVENT_BUS_MAX_RETRIES", "5"))
RETRY_DELAY_SECONDS: float = float(os.getenv("EVENT_BUS_RETRY_DELAY_SECONDS", "2"))
HANDLER_TIMEOUT_SECONDS: float = float(os.getenv("EVENT_BUS_HANDLER_TIMEOUT_SECONDS", "30"))
DEFAULT_WORKER_COUNT: int = int(os.getenv("EVENT_BUS_WORKER_COUNT", "2"))
POLL_INTERVAL_SECONDS: float = float(os.getenv("EVENT_BUS_POLL_INTERVAL_SECONDS", "1"))


def compute_backoff_seconds(attempt: int) -> float:
    """Exponential backoff from base retry delay."""
    if attempt <= 0:
        return 0.0
    return RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
