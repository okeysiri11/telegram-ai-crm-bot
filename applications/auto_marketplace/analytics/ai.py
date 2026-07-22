# AI Analytics — aggregate Sprint 10.3 intelligence metrics.

from __future__ import annotations

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AIAnalyticsEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def summary(self) -> dict:
        return {
            "recommendations": self._store.smart_recommendations.count(),
            "price_insights": self._store.ai_price_insights.count(),
            "inspections": self._store.ai_inspection_results.count(),
            "forecasts": self._store.vehicle_forecasts.count(),
            "assistant_replies": self._store.assistant_replies.count(),
            "knowledge_cards": self._store.vehicle_knowledge_cards.count(),
            "risk_scores": self._store.ai_risk_scores.count(),
        }


ai_analytics_engine = AIAnalyticsEngine()
