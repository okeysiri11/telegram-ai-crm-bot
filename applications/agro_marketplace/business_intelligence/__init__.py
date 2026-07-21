"""Business intelligence package."""

from __future__ import annotations

from typing import Any

__all__ = ["BusinessIntelligenceEngine", "business_intelligence_engine"]


def __getattr__(name: str) -> Any:
    if name in {"BusinessIntelligenceEngine", "business_intelligence_engine"}:
        from applications.agro_marketplace.business_intelligence.engine import (
            BusinessIntelligenceEngine,
            business_intelligence_engine,
        )

        return BusinessIntelligenceEngine if name == "BusinessIntelligenceEngine" else business_intelligence_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
