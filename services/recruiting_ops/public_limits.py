"""Vanguard public apply/event rate limits — server-side, env-configurable.

Policy (documented in SPRINT_RECRUITING_1_5 RESULT):
- Apply: per client IP and per email, sliding 60s window.
- Events: per client IP, higher ceiling (tracking must not starve apply).
- Defaults: development 20 apply/min, production 8 apply/min.
- Store: Redis when reachable (shared=true). Development without Redis uses
process_local (shared=false). Production without Redis is fail-closed
(store_unavailable, never silent process_local, never SHARED=YES).
- Frontend controls are ignored; HTTP 429 + Retry-After on exceed.
"""

from __future__ import annotations

import os
from typing import Any

from services.recruiting_ops.runtime import is_production_runtime
from services.recruiting_ops.shared_store import get_store, reset_shared_store_for_tests


def reset_public_limits_for_tests() -> None:
    reset_shared_store_for_tests()


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
    store = get_store()
    result = store.hit_rate(key, limit, window_seconds())
    result["store"] = store.backend
    result["shared"] = store.shared
    return result
