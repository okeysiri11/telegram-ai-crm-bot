# Market AI — market trends, opportunities, demand/supply signals.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.ai.knowledge import AgroKnowledgeService, agro_knowledge
from applications.agro_marketplace.ai.models import KnowledgeKind
from applications.agro_marketplace.forecasting.engine import ForecastingEngine, forecasting_engine
from applications.agro_marketplace.recommendations.engine import RecommendationEngine, recommendation_engine
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class MarketAIService:
    def __init__(
        self,
        store: AgroStore | None = None,
        knowledge: AgroKnowledgeService | None = None,
        forecasting: ForecastingEngine | None = None,
        recommendations: RecommendationEngine | None = None,
    ) -> None:
        self._store = store or agro_store
        self._knowledge = knowledge or agro_knowledge
        self._forecasting = forecasting or forecasting_engine
        self._recommendations = recommendations or recommendation_engine

    def trends(self, *, query: str = "") -> list[dict[str, Any]]:
        return self._knowledge.search(query or "market", kind=KnowledgeKind.MARKET_TREND)

    async def market_snapshot(self, subject: str, *, region: str = "") -> dict[str, Any]:
        demand = await self._forecasting.forecast_demand(subject, region=region)
        supply = await self._forecasting.forecast_supply(subject, region=region)
        price = await self._forecasting.forecast_price(subject, region=region)
        opportunities = await self._recommendations.detect_trade_opportunities()
        return {
            "subject": subject,
            "region": region,
            "demand": demand.to_dict(),
            "supply": supply.to_dict(),
            "price": price.to_dict(),
            "opportunities": opportunities.to_dict(),
            "trends": self.trends(query=subject),
        }


market_ai_service = MarketAIService()
