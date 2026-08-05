"""Lazy public exports — Sprint 35.0 coupling reduction (same public interface)."""

from __future__ import annotations

from typing import Any

__all__ = [
    "PlatformStateService",
    "platform_state",
    "SyncEngine",
    "sync_engine",
    "enterprise_runtime",
    "telegram_runtime",
    "web_runtime",
    "desktop_runtime",
    "mobile_runtime",
    "api_runtime",
    "ai_runtime",
]


def __getattr__(name: str) -> Any:
    if name in {"PlatformStateService", "platform_state"}:
        from platform_state.service import PlatformStateService, platform_state

        return PlatformStateService if name == "PlatformStateService" else platform_state
    if name in {"SyncEngine", "sync_engine"}:
        from platform_state.sync_engine import SyncEngine, sync_engine

        return SyncEngine if name == "SyncEngine" else sync_engine
    if name == "enterprise_runtime":
        from platform_state.enterprise import enterprise_runtime

        return enterprise_runtime
    if name.endswith("_runtime"):
        from platform_state import clients as _clients

        return getattr(_clients, name)
    raise AttributeError(f"module 'platform_state' has no attribute {name!r}")
