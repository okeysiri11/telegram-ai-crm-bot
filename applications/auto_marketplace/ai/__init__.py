"""Auto AI package — Sprint 10.3 vehicle intelligence facade."""

from __future__ import annotations

from typing import Any

__all__ = ["AutoAIDomainEngine", "auto_ai_domain_engine"]


def __getattr__(name: str) -> Any:
    if name in {"AutoAIDomainEngine", "auto_ai_domain_engine"}:
        from applications.auto_marketplace.ai.facade import AutoAIDomainEngine, auto_ai_domain_engine

        return AutoAIDomainEngine if name == "AutoAIDomainEngine" else auto_ai_domain_engine
    raise AttributeError(name)
