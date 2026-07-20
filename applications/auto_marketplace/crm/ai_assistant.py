# AI Sales Assistant — lead scoring, intent, predictions via Platform Core bridges.

from __future__ import annotations

import logging
from typing import Any

from applications.auto_marketplace.crm.models import CRMDeal, CRMLead, CustomerProfile

logger = logging.getLogger(__name__)


class AISalesAssistant:
    @staticmethod
    async def score_lead(lead: CRMLead, customer: CustomerProfile | None = None) -> float:
        score = 20.0
        if lead.source.value in {"referral", "dealer"}:
            score += 20
        if lead.vehicle_id:
            score += 15
        if customer and customer.email:
            score += 10
        if customer and customer.phone:
            score += 10
        try:
            from platform_decision import decision_engine
            from platform_decision.models import DecisionContext

            result = await decision_engine.decide(
                DecisionContext(
                    request="lead_scoring",
                    metadata={"lead": lead.to_dict(), "customer": customer.to_dict() if customer else {}},
                )
            )
            if hasattr(result, "confidence"):
                score = min(100.0, score + result.confidence * 30)
        except Exception:
            logger.debug("decision engine unavailable for lead scoring")
        return min(score, 100.0)

    @staticmethod
    async def analyze_intent(customer: CustomerProfile, interactions: list[dict]) -> dict[str, Any]:
        try:
            from platform_reasoning import reasoning_engine
            from platform_reasoning.models import ReasoningContext

            session = await reasoning_engine.reason(
                ReasoningContext(
                    request="Analyze customer purchase intent",
                    metadata={"customer": customer.to_dict(), "interactions": interactions[-10:]},
                )
            )
            return {"intent_score": customer.intent_score, "analysis": getattr(session, "conclusion", {})}
        except Exception:
            return {"intent_score": customer.intent_score, "analysis": "moderate_interest"}

    @staticmethod
    async def next_best_action(lead: CRMLead, deal: CRMDeal | None = None) -> dict[str, Any]:
        if lead.status.value == "new":
            return {"action": "call", "priority": "high", "message": "Initial contact within 15 minutes"}
        if deal and deal.stage.value == "negotiation":
            return {"action": "send_offer", "priority": "high", "message": "Send revised offer"}
        return {"action": "follow_up_email", "priority": "medium", "message": "Schedule follow-up"}

    @staticmethod
    async def suggest_follow_up(lead: CRMLead) -> dict[str, Any]:
        return {
            "channel": "email",
            "delay_hours": 24,
            "template": "follow_up_vehicle_inquiry",
            "lead_id": lead.lead_id,
        }

    @staticmethod
    async def summarize_conversation(interactions: list[dict]) -> str:
        if not interactions:
            return "No interactions yet."
        texts = [i.get("body", i.get("subject", "")) for i in interactions[-5:]]
        summary = " | ".join(t for t in texts if t)[:500]
        return summary or "Recent activity logged."

    @staticmethod
    async def predict_deal_probability(deal: CRMDeal) -> float:
        stage_probs = {
            "prospect": 0.1,
            "qualification": 0.25,
            "proposal": 0.45,
            "negotiation": 0.65,
            "approval": 0.85,
            "closed_won": 1.0,
            "closed_lost": 0.0,
        }
        return stage_probs.get(deal.stage.value, 0.2)

    @staticmethod
    async def segment_customer(customer: CustomerProfile) -> str:
        if customer.lifetime_value > 100000:
            return "vip"
        if customer.intent_score > 70:
            return "hot"
        if customer.intent_score > 40:
            return "warm"
        return "cold"


ai_sales_assistant = AISalesAssistant()
