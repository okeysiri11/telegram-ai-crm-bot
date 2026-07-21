"""Mobile package."""

from __future__ import annotations

from typing import Any

__all__ = ["MobileEngine", "mobile_engine"]


def __getattr__(name: str) -> Any:
    if name in {"MobileEngine", "mobile_engine"}:
        from applications.agro_marketplace.mobile.engine import MobileEngine, mobile_engine

        return MobileEngine if name == "MobileEngine" else mobile_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
