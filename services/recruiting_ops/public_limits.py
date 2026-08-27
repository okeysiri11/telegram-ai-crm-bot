"""Vanguard public apply/event rate limits — server-side, env-configurable.

Policy (documented in SPRINT_RECRUITING_1_4 RESULT):
- Apply: per client IP and per email, sliding 60s window.
- Events: per client IP, higher ceiling (tracking must not starve apply).
- Defaults: development 20 apply/min, production 8 apply/min.
- Frontend controls are ignored; HTTP 429 + Retry-After on exceed.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from typing import Any

from services.recruiting_ops.runtime import is_production_runtime

_WINDOWS: dict[str, deque[float]] = defaultdict(deque)


def reset_public_limits_for_tests() -> None:
    _WINDOWS.clear()


def _int_env(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def apply_limit() -> int:
    default = 8 if is_production_runtime() else 20
    return _int_env("VANGUARD_APPLY_RATE_LIMIT", default)


def events_limit() -> int:
    return _int_env("VANGUARD_EVENTS_RATE_LIMIT", 60)


def window_seconds() -> int:
    return _int_env("VANGUARD_RATE_WINDOW_SECONDS", 60)


def check_rate_limit(*, key: str, limit: int) -> dict[str, Any]:
    now = time.monotonic()
    span = float(window_seconds())
    bucket = _WINDOWS[key]
    while bucket and now - bucket[0] > span:
        bucket.popleft()
    if len(bucket) >= limit:
        retry = max(1, int(span - (now - bucket[0])))
        return {
            "allowed": False,
            "error": "rate_limited",
            "retry_after_seconds": retry,
            "limit": limit,
            "message_ru": "Слишком много заявок. Подождите и повторите.",
        }
    bucket.append(now)
    return {"allowed": True, "limit": limit, "remaining": max(0, limit - len(bucket))}
