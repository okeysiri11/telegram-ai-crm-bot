"""Runtime flags for Recruiting Ops persistence."""

from __future__ import annotations

import os


def current_environment() -> str:
    return (os.getenv("ENVIRONMENT") or os.getenv("ADOS_ENV") or "development").strip().lower()


def is_production_runtime() -> bool:
    return current_environment() in {"production", "prod", "staging"}


def memory_fallback_allowed() -> bool:
    """Volatile memory is DEV/test only. Production must not pretend a memory lead is stored."""
    if os.getenv("RECRUITING_ALLOW_MEMORY_FALLBACK", "").strip().lower() in {"1", "true", "yes"}:
        return not is_production_runtime()
    return not is_production_runtime()
