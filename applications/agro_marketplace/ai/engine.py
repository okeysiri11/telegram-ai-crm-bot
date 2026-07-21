# AgroAIEngine — facade for agricultural AI layer (Sprint 8.4).

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.agents.service import AgroAgentService, agent_service
from applications.agro_marketplace.ai.knowledge import AgroKnowledgeService, agro_knowledge
from applications.agro_marketplace.ai.workflow import AgroAIWorkflow, agro_ai_workflow
from applications.agro_marketplace.assistant.service import AgroAssistantService, agro_assistant
from applications.agro_marketplace.crop_ai.service import CropAIService, crop_ai_service
from applications.agro_marketplace.forecasting.engine import ForecastingEngine, forecasting_engine
from applications.agro_marketplace.market_ai.service import MarketAIService, market_ai_service
from applications.agro_marketplace.pricing_ai.service import PricingAIService, pricing_ai_service
from applications.agro_marketplace.recommendations.engine import RecommendationEngine, recommendation_engine
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class AgroAIEngine:
    """Agricultural AI workforce — agents, recommendations, forecasting, knowledge."""

    def __init__(
        self,
        store: AgroStore | None = None,
        agents: AgroAgentService | None = None,
        recommendations: RecommendationEngine | None = None,
        forecasting: ForecastingEngine | None = None,
        knowledge: AgroKnowledgeService | None = None,
        pricing_ai: PricingAIService | None = None,
        crop_ai: CropAIService | None = None,
        market_ai: MarketAIService | None = None,
        assistant: AgroAssistantService | None = None,
        workflow: AgroAIWorkflow | None = None,
    ) -> None:
        self._store = store or agro_store
        self.agents = agents or agent_service
        self.recommendations = recommendations or recommendation_engine
        self.forecasting = forecasting or forecasting_engine
        self.knowledge = knowledge or agro_knowledge
        self.pricing_ai = pricing_ai or pricing_ai_service
        self.crop_ai = crop_ai or crop_ai_service
        self.market_ai = market_ai or market_ai_service
        self.assistant = assistant or agro_assistant
        self.workflow = workflow or agro_ai_workflow

    def metrics(self) -> dict[str, Any]:
        self.agents.registry._ensure_seeded()
        self.knowledge._ensure_seeded()
        return {
            "agro_ai": "1.0",
            "agents": self.agents.metrics(),
            "recommendations": self._store.recommendations.count(),
            "forecasts": self._store.forecasts.count(),
            "knowledge": self.knowledge.metrics(),
            "executive_reports": self._store.executive_reports.count(),
            "ai_tasks": self._store.ai_workflow_tasks.count(),
            "invocations": self._store.agent_invocations.count(),
        }


agro_ai_engine = AgroAIEngine()
