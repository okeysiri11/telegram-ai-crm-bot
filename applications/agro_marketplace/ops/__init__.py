"""Ops package — production validation and commercial release."""

from __future__ import annotations

from typing import Any

__all__ = ["OpsEngine", "ops_engine"]


def __getattr__(name: str) -> Any:
    if name in {"OpsEngine", "ops_engine"}:
        from applications.agro_marketplace.ops.engine import OpsEngine, ops_engine

        return OpsEngine if name == "OpsEngine" else ops_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
