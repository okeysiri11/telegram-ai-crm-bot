"""Recommendations package — AI sales recommendations and smart engine."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AIRecommendationEngine",
    "ai_recommendation_engine",
    "SmartRecommendationEngine",
    "smart_recommendation_engine",
]


def __getattr__(name: str) -> Any:
    if name in {"AIRecommendationEngine", "ai_recommendation_engine"}:
        from applications.auto_marketplace.recommendations.service import (
            AIRecommendationEngine,
            ai_recommendation_engine,
        )

        return AIRecommendationEngine if name == "AIRecommendationEngine" else ai_recommendation_engine
    if name in {"SmartRecommendationEngine", "smart_recommendation_engine"}:
        from applications.auto_marketplace.recommendations.smart import (
            SmartRecommendationEngine,
            smart_recommendation_engine,
        )

        return SmartRecommendationEngine if name == "SmartRecommendationEngine" else smart_recommendation_engine
    raise AttributeError(name)
