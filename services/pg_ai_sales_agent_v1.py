# AI Sales Agent v1 — product layer over sales agent engine.

from __future__ import annotations

import uuid
from typing import Any

from services.pg_ai_sales_agent_engine import AiSalesAgentError, AiSalesAgentV1
from database.models.ai_sales_agent import SalesLeadStatus

SALES_FEATURES = frozenset({
    "lead_qualification",
    "customer_intent_detection",
    "budget_estimation",
    "vehicle_recommendation",
    "offer_generation",
    "follow_up_reminders",
})


class SalesAgentError(Exception):
    pass


class SalesAgentV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await AiSalesAgentV1.user_can_access(user_id)

    @staticmethod
    def list_features() -> list[dict[str, str]]:
        labels = {
            "lead_qualification": "Lead Qualification",
            "customer_intent_detection": "Customer Intent Detection",
            "budget_estimation": "Budget Estimation",
            "vehicle_recommendation": "Vehicle Recommendation",
            "offer_generation": "Offer Generation",
            "follow_up_reminders": "Follow-up Reminders",
        }
        return [{"code": k, "label": labels[k]} for k in sorted(SALES_FEATURES)]

    @staticmethod
    async def _wrap(coro):
        try:
            return await coro
        except AiSalesAgentError as exc:
            raise SalesAgentError(str(exc)) from exc

    @staticmethod
    async def get_agent(actor_id: int, tenant_id: uuid.UUID) -> dict[str, Any]:
        dashboard = await SalesAgentV1._wrap(
            AiSalesAgentV1.get_agent_dashboard(actor_id, tenant_id)
        )
        return {
            **dashboard,
            "features": list(SALES_FEATURES),
            "feature_data": {
                "lead_qualification": await SalesAgentV1.get_lead_qualification_module(
                    actor_id, tenant_id
                ),
                "follow_up_reminders": await SalesAgentV1.get_follow_up_reminders_module(
                    actor_id, tenant_id
                ),
            },
        }

    @staticmethod
    async def get_feature(
        actor_id: int,
        tenant_id: uuid.UUID,
        feature: str,
    ) -> dict[str, Any]:
        if feature not in SALES_FEATURES:
            raise SalesAgentError(f"Unknown feature: {feature}")
        return await {
            "lead_qualification": lambda: SalesAgentV1.get_lead_qualification_module(
                actor_id, tenant_id
            ),
            "customer_intent_detection": lambda: SalesAgentV1.get_intent_detection_module(
                actor_id, tenant_id
            ),
            "budget_estimation": lambda: SalesAgentV1.get_budget_estimation_module(
                actor_id, tenant_id
            ),
            "vehicle_recommendation": lambda: SalesAgentV1.get_vehicle_recommendation_module(
                actor_id, tenant_id
            ),
            "offer_generation": lambda: SalesAgentV1.get_offer_generation_module(
                actor_id, tenant_id
            ),
            "follow_up_reminders": lambda: SalesAgentV1.get_follow_up_reminders_module(
                actor_id, tenant_id
            ),
        }[feature]()

    @staticmethod
    async def get_lead_qualification_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        leads = await AiSalesAgentV1.list_leads(actor_id, tenant_id, limit=20)
        qualified = [l for l in leads if l["status"] == "QUALIFIED"]
        return {
            "feature": "lead_qualification",
            "total_leads": len(leads),
            "qualified_leads": len(qualified),
            "statuses": [s.value for s in SalesLeadStatus],
            "recent_leads": leads[:10],
        }

    @staticmethod
    async def get_intent_detection_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        leads = await AiSalesAgentV1.list_leads(actor_id, tenant_id, limit=20)
        with_intent = [l for l in leads if l.get("intent")]
        return {
            "feature": "customer_intent_detection",
            "leads_with_intent": len(with_intent),
            "intents": list({l["intent"] for l in with_intent if l.get("intent")}),
            "leads": with_intent[:10],
        }

    @staticmethod
    async def get_budget_estimation_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        leads = await AiSalesAgentV1.list_leads(actor_id, tenant_id, limit=20)
        with_budget = [
            l for l in leads if l.get("budget_min") or l.get("budget_max")
        ]
        return {
            "feature": "budget_estimation",
            "leads_with_budget": len(with_budget),
            "leads": with_budget[:10],
        }

    @staticmethod
    async def get_vehicle_recommendation_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        leads = await AiSalesAgentV1.list_leads(actor_id, tenant_id, limit=10)
        recommendations: list[dict[str, Any]] = []
        for lead in leads[:3]:
            try:
                rec = await AiSalesAgentV1.recommend_vehicles(
                    actor_id, tenant_id, uuid.UUID(lead["id"]), limit=3
                )
                recommendations.append(rec)
            except AiSalesAgentError:
                continue
        return {
            "feature": "vehicle_recommendation",
            "recommendations": recommendations,
            "integration": "car_engine",
        }

    @staticmethod
    async def get_offer_generation_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        leads = await AiSalesAgentV1.list_leads(
            actor_id, tenant_id, status="OFFER_SENT", limit=20
        )
        return {
            "feature": "offer_generation",
            "offers_sent_count": len(leads),
            "leads": leads[:10],
            "integration": "document_engine",
        }

    @staticmethod
    async def get_follow_up_reminders_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        result = await AiSalesAgentV1.process_follow_up_reminders(actor_id, tenant_id)
        return {"feature": "follow_up_reminders", **result}
