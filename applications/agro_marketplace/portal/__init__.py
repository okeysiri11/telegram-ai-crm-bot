"""Portal package."""

from __future__ import annotations

from typing import Any

__all__ = ["PortalEngine", "portal_engine"]


def __getattr__(name: str) -> Any:
    if name in {"PortalEngine", "portal_engine"}:
        from applications.agro_marketplace.portal.engine import PortalEngine, portal_engine

        return PortalEngine if name == "PortalEngine" else portal_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
