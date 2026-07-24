"""AI Business Advisor library facade — Sprint 22.1."""

from __future__ import annotations

from typing import Any

from platform_ai_business_advisor.approval import OwnerApproval
from platform_ai_business_advisor.brief import DailyBrief
from platform_ai_business_advisor.forecast import ForecastEngine
from platform_ai_business_advisor.health import BusinessHealthAnalyzer
from platform_ai_business_advisor.integrations import AdvisorIntegrations
from platform_ai_business_advisor.models import INDUSTRIES, PRINCIPLES
from platform_ai_business_advisor.opportunities import OpportunityDetector
from platform_ai_business_advisor.recommendations import RecommendationEngine


class AIBusinessAdvisorLibrary:
    def __init__(self) -> None:
        self.health = BusinessHealthAnalyzer()
        self.opportunities = OpportunityDetector()
        self.recommendations = RecommendationEngine()
        self.forecast = ForecastEngine()
        self.brief = DailyBrief()
        self.integrations = AdvisorIntegrations()
        self.approval = OwnerApproval()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def industries(self) -> list[str]:
        return list(INDUSTRIES)

    def run_cycle(self, *, industry: str = "generic", snapshot: dict[str, float] | None = None) -> dict[str, Any]:
        health = self.health.analyze(industry=industry, snapshot=snapshot)
        opps = self.opportunities.detect(health)
        recs = self.recommendations.recommend(opps)
        forecasts = self.forecast.forecast(health)
        brief = self.brief.generate(health=health, opportunities=opps, recommendations=recs, forecasts=forecasts)
        handoffs = [self.integrations.to_product_intelligence(r) for r in recs["recommendations"][:3]]
        return {
            "health": health,
            "opportunities": opps,
            "recommendations": recs,
            "forecasts": forecasts,
            "brief": brief,
            "product_intelligence_handoffs": handoffs,
            "ai_executes_automatically": False,
        }

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        cycle = self.run_cycle(industry="retail")
        owner = self.approval.decide(decision="approve", owner_id="business_owner", notes="Review daily brief")
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "industries": self.industries(),
            "industry": cycle["health"]["industry"],
            "overall_health": cycle["health"]["overall"],
            "opportunities": cycle["opportunities"]["count"],
            "recommendations": cycle["recommendations"]["count"],
            "forecasts": len(cycle["forecasts"]["forecasts"]),
            "brief_ready": cycle["brief"]["passed"],
            "integrations_linked": links["linked"],
            "product_intelligence_handoffs": len(cycle["product_intelligence_handoffs"]),
            "ai_never_executes": True,
            "owner_approval_required": True,
            "owner_decision": owner["decision"],
            "status": "ready",
            "integrations": links,
            "full": {**cycle, "owner": owner, "links": links},
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": ["health", "opportunities", "recommendations", "forecast", "brief", "approval"],
            "principles": self.principles(),
            "industries": self.industries(),
        }


ai_business_advisor_library = AIBusinessAdvisorLibrary()
