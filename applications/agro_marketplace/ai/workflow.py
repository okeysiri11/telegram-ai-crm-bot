# AI workflow automation — negotiations, lead qualification, matching, reporting, tasks.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from applications.agro_marketplace.ai.events import (
    ExecutiveReportGeneratedEvent,
    LeadQualifiedAIEvent,
    TradeOpportunityDetectedEvent,
)
from applications.agro_marketplace.ai.models import AIWorkflowTask, ExecutiveReport
from applications.agro_marketplace.crm.engine import CRMEngine, crm_engine
from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.agro_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.agro_marketplace.marketplace.engine import MarketplaceEngine, marketplace_engine
from applications.agro_marketplace.negotiations.engine import NegotiationEngine, negotiation_engine
from applications.agro_marketplace.recommendations.engine import RecommendationEngine, recommendation_engine
from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class AgroAIWorkflow:
    def __init__(
        self,
        store: AgroStore | None = None,
        crm: CRMEngine | None = None,
        marketplace: MarketplaceEngine | None = None,
        negotiations: NegotiationEngine | None = None,
        recommendations: RecommendationEngine | None = None,
        platform: PlatformBridge | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self._store = store or agro_store
        self._crm = crm or crm_engine
        self._marketplace = marketplace or marketplace_engine
        self._negotiations = negotiations or negotiation_engine
        self._recommendations = recommendations or recommendation_engine
        self._platform = platform or platform_bridge
        self._ecosystem = ecosystem or ecosystem_bridge

    def _task(self, title: str, task_type: str, related_id: str, agent: str, payload: dict | None = None) -> AIWorkflowTask:
        task = AIWorkflowTask(
            title=title,
            task_type=task_type,
            related_id=related_id,
            assignee_agent=agent,
            payload=payload or {},
        )
        return self._store.ai_workflow_tasks.save(task.task_id, task)

    async def assist_negotiation(self, negotiation_id: str, *, target_price: float = 0.0) -> dict[str, Any]:
        suggestion = await self._negotiations.assistant_suggestion(
            negotiation_id, target_price=target_price
        )
        await self._platform.start_ai_workflow(
            "negotiation",
            {"negotiation_id": negotiation_id, "suggestion": suggestion},
        )
        task = self._task(
            "AI negotiation assist",
            "negotiation",
            negotiation_id,
            "pricing_advisor",
            suggestion,
        )
        return {"suggestion": suggestion, "task": task.to_dict()}

    async def qualify_lead(self, lead_id: str) -> dict[str, Any]:
        lead = self._crm.get_lead(lead_id)
        qualified = self._crm.qualify_lead(lead_id) if lead.score >= 60 else lead
        auto_qualified = qualified.score >= 60
        if auto_qualified and qualified.status.value != "qualified":
            qualified = self._crm.qualify_lead(lead_id)
        await publish(
            LeadQualifiedAIEvent(
                lead_id=lead_id,
                score=qualified.score,
                qualified=auto_qualified or qualified.status.value == "qualified",
            )
        )
        await self._platform.start_ai_workflow("lead_qualification", {"lead_id": lead_id})
        task = self._task(
            "AI lead qualification",
            "lead_qualification",
            lead_id,
            "marketplace_moderator",
            {"score": qualified.score},
        )
        return {"lead": qualified.to_dict(), "qualified": True, "task": task.to_dict()}

    async def auto_match_offers(self) -> dict[str, Any]:
        matches = []
        for offer in self._marketplace.list_offers():
            if offer.status.value != "published":
                continue
            result = await self._marketplace.match_offer(offer.offer_id)
            if result.get("matched"):
                matches.append(result)
                self._task(
                    "Auto offer match",
                    "offer_matching",
                    offer.offer_id,
                    "marketplace_moderator",
                    result,
                )
        return {"matched": len(matches), "items": matches}

    async def detect_opportunities(self) -> dict[str, Any]:
        recommendation = await self._recommendations.detect_trade_opportunities()
        await publish(
            TradeOpportunityDetectedEvent(
                opportunity_count=len(recommendation.items),
                top_score=recommendation.score,
                opportunities=recommendation.items[:10],
            )
        )
        return recommendation.to_dict()

    async def executive_report(self, *, title: str = "Agro Executive Report") -> ExecutiveReport:
        metrics = {
            "crm": self._crm.metrics(),
            "marketplace": self._marketplace.metrics(),
            "products": self._store.agro_products.count(),
            "warehouses": self._store.agro_warehouses.count(),
            "inventory": self._store.inventory_items.count(),
            "forecasts": self._store.forecasts.count(),
            "recommendations": self._store.recommendations.count(),
        }
        brief = await self._ecosystem.executive_brief(title, metrics=metrics)
        opportunities = await self._recommendations.detect_trade_opportunities()
        report = ExecutiveReport(
            title=title,
            summary=str(brief.get("brief") or brief.get("summary") or "Agro marketplace executive overview"),
            sections=[
                {"name": "CRM", "data": metrics["crm"]},
                {"name": "Marketplace", "data": metrics["marketplace"]},
                {"name": "Opportunities", "data": opportunities.items[:5]},
                {"name": "Executive brief", "data": brief},
            ],
            metrics=metrics,
            recommendations=[
                "Prioritize top trade opportunities",
                "Rebalance warehouse utilization",
                "Qualify high-score leads automatically",
            ],
        )
        saved = self._store.executive_reports.save(report.report_id, report)
        await publish(
            ExecutiveReportGeneratedEvent(report_id=saved.report_id, title=saved.title)
        )
        self._task("Executive report", "executive_reporting", saved.report_id, "executive_agro_ai")
        await self._platform.start_ai_workflow("executive_report", {"report_id": saved.report_id})
        return saved

    def list_tasks(self) -> list[AIWorkflowTask]:
        return self._store.ai_workflow_tasks.list_all()

    def get_report(self, report_id: str) -> ExecutiveReport:
        report = self._store.executive_reports.get(report_id)
        if report is None:
            raise NotFoundError("ExecutiveReport", report_id)
        return report


agro_ai_workflow = AgroAIWorkflow()
