"""Enterprise domain — Sprint 10.8."""

from __future__ import annotations

from typing import Any

__all__ = ["EnterpriseDomainEngine", "enterprise_domain_engine"]


def __getattr__(name: str) -> Any:
    if name in {"EnterpriseDomainEngine", "enterprise_domain_engine"}:
        from applications.auto_marketplace.enterprise.facade import (
            EnterpriseDomainEngine,
            enterprise_domain_engine,
        )

        return EnterpriseDomainEngine if name == "EnterpriseDomainEngine" else enterprise_domain_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
