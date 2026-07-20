# AISalesEngine — unified AI Sales & Customer Intelligence facade.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.ai_sales.agents import AGENT_REGISTRY, BaseAIAgent
from applications.auto_marketplace.ai_sales.integration import AISalesPlatformBridge, ai_sales_platform_bridge
from applications.auto_marketplace.ai_sales.models import AgentType
from applications.auto_marketplace.ai_sales.workflow_bridge import AISalesWorkflowBridge, ai_sales_workflow_bridge
from applications.auto_marketplace.conversation.service import ConversationService, conversation_service
from applications.auto_marketplace.customer_intelligence.service import (
    CustomerIntelligenceService,
    customer_intelligence_service,
)
from applications.auto_marketplace.knowledge.service import KnowledgeService, knowledge_service
from applications.auto_marketplace.lead_intelligence.service import LeadIntelligenceService, lead_intelligence_service
from applications.auto_marketplace.negotiation.service import NegotiationService, negotiation_service
from applications.auto_marketplace.recommendations.service import AIRecommendationEngine, ai_recommendation_engine
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AISalesEngine:
    """Enterprise AI Sales Agents & Customer Intelligence entry point."""

    def __init__(
        self,
        store: MarketplaceStore | None = None,
        intelligence: CustomerIntelligenceService | None = None,
        recommendations: AIRecommendationEngine | None = None,
        conversations: ConversationService | None = None,
        lead_intelligence: LeadIntelligenceService | None = None,
        negotiation: NegotiationService | None = None,
        knowledge: KnowledgeService | None = None,
        workflow: AISalesWorkflowBridge | None = None,
        platform: AISalesPlatformBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self.intelligence = intelligence or customer_intelligence_service
        self.recommendations = recommendations or ai_recommendation_engine
        self.conversations = conversations or conversation_service
        self.leads = lead_intelligence or lead_intelligence_service
        self.negotiation = negotiation or negotiation_service
        self.knowledge = knowledge or knowledge_service
        self.workflow = workflow or ai_sales_workflow_bridge
        self.platform = platform or ai_sales_platform_bridge

    def get_agent(self, agent_type: AgentType | str) -> BaseAIAgent:
        if isinstance(agent_type, str):
            agent_type = AgentType(agent_type)
        return AGENT_REGISTRY[agent_type]

    async def dispatch_agent(self, agent_type: AgentType | str, context: dict[str, Any]) -> dict[str, Any]:
        agent = self.get_agent(agent_type)
        return await agent.handle(context)

    def metrics(self) -> dict[str, Any]:
        return {
            "conversation_sessions": self._store.conversation_sessions.count(),
            "intelligence_profiles": self._store.intelligence_profiles.count(),
            "ai_offers": self._store.ai_offers.count(),
            "knowledge_articles": self._store.knowledge_articles.count(),
            "agents": [a.value for a in AgentType],
        }


ai_sales_engine = AISalesEngine()
