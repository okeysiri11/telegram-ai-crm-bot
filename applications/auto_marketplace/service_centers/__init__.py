"""Service centers domain — Sprint 10.5."""

from __future__ import annotations

from typing import Any

__all__ = [
    "ServiceDomainEngine",
    "service_domain_engine",
    "ServiceCenterEngine",
    "service_center_engine",
]


def __getattr__(name: str) -> Any:
    if name in {"ServiceDomainEngine", "service_domain_engine"}:
        from applications.auto_marketplace.service_centers.facade import (
            ServiceDomainEngine,
            service_domain_engine,
        )

        return ServiceDomainEngine if name == "ServiceDomainEngine" else service_domain_engine
    if name in {"ServiceCenterEngine", "service_center_engine"}:
        from applications.auto_marketplace.service_centers.engine import (
            ServiceCenterEngine,
            service_center_engine,
        )

        return ServiceCenterEngine if name == "ServiceCenterEngine" else service_center_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
