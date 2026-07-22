"""Transport / logistics domain — Sprint 10.6."""

from __future__ import annotations

from typing import Any

__all__ = [
    "LogisticsDomainEngine",
    "logistics_domain_engine",
    "TransportEngine",
    "transport_engine",
]


def __getattr__(name: str) -> Any:
    if name in {"LogisticsDomainEngine", "logistics_domain_engine"}:
        from applications.auto_marketplace.transport.facade import (
            LogisticsDomainEngine,
            logistics_domain_engine,
        )

        return LogisticsDomainEngine if name == "LogisticsDomainEngine" else logistics_domain_engine
    if name in {"TransportEngine", "transport_engine"}:
        from applications.auto_marketplace.transport.engine import TransportEngine, transport_engine

        return TransportEngine if name == "TransportEngine" else transport_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
