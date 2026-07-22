# Auto AI domain facade — Sprint 10.3.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.analytics.ai import AIAnalyticsEngine, ai_analytics_engine
from applications.auto_marketplace.assistant.engine import BuyerAssistantEngine, buyer_assistant_engine
from applications.auto_marketplace.forecasting.vehicle import VehicleForecastEngine, vehicle_forecast_engine
from applications.auto_marketplace.inspection_ai.engine import InspectionAIEngine, inspection_ai_engine
from applications.auto_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.auto_marketplace.knowledge.vehicle import VehicleKnowledgeEngine, vehicle_knowledge_engine
from applications.auto_marketplace.matching.engine import MatchingEngine, matching_engine
from applications.auto_marketplace.pricing_ai.engine import PricingAIEngine, pricing_ai_engine
from applications.auto_marketplace.recommendations.smart import SmartRecommendationEngine, smart_recommendation_engine
from applications.auto_marketplace.risk.engine import RiskEngine, risk_engine


class AutoAIDomainEngine:
    """Sprint 10.3 facade — recommendations, pricing AI, inspection AI, forecast, assistant."""

    def __init__(
        self,
        recommendations: SmartRecommendationEngine | None = None,
        matching: MatchingEngine | None = None,
        pricing_ai: PricingAIEngine | None = None,
        inspection_ai: InspectionAIEngine | None = None,
        forecasting: VehicleForecastEngine | None = None,
        risk: RiskEngine | None = None,
        assistant: BuyerAssistantEngine | None = None,
        knowledge: VehicleKnowledgeEngine | None = None,
        analytics: AIAnalyticsEngine | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self.recommendations = recommendations or smart_recommendation_engine
        self.matching = matching or matching_engine
        self.pricing_ai = pricing_ai or pricing_ai_engine
        self.inspection_ai = inspection_ai or inspection_ai_engine
        self.forecasting = forecasting or vehicle_forecast_engine
        self.risk = risk or risk_engine
        self.assistant = assistant or buyer_assistant_engine
        self.knowledge = knowledge or vehicle_knowledge_engine
        self.analytics = analytics or ai_analytics_engine
        self._platform = platform or platform_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            **self.analytics.summary(),
            "matching": self.matching.metrics(),
            "recommendations": self.recommendations.metrics(),
            "pricing_ai": self.pricing_ai.metrics(),
            "inspection_ai": self.inspection_ai.metrics(),
            "forecasting": self.forecasting.metrics(),
            "risk": self.risk.metrics(),
            "assistant": self.assistant.metrics(),
            "knowledge": self.knowledge.metrics(),
        }

    async def remember_snapshot(self) -> None:
        await self._platform.store_customer_context("auto_ai:snapshot", self.metrics())


auto_ai_domain_engine = AutoAIDomainEngine()
