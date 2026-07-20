# Lead Intelligence — scoring, qualification, priority, forecasting.

from __future__ import annotations

from events.publisher import publish

from applications.auto_marketplace.ai_sales.events import AISalesLeadQualifiedEvent, CustomerIntentDetectedEvent
from applications.auto_marketplace.ai_sales.integration import ai_sales_platform_bridge
from applications.auto_marketplace.ai_sales.models import LeadIntelligenceReport, LeadTemperature
from applications.auto_marketplace.crm.models import CRMLead, CustomerProfile
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class LeadIntelligenceService:
    QUALIFY_THRESHOLD = 60.0

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    async def analyze_lead(self, lead_id: str) -> LeadIntelligenceReport:
        lead = self._store.crm_leads.get(lead_id)
        if lead is None:
            raise ValueError(f"Lead not found: {lead_id}")
        customer = self._store.customer_profiles.get(lead.customer_id)
        score = await self._compute_score(lead, customer)
        temperature = self._classify_temperature(score)
        probability = min(score / 100.0, 0.95)
        expected_value = self._estimate_deal_value(lead, customer)
        priority = 1 if temperature == LeadTemperature.HOT else 2 if temperature == LeadTemperature.WARM else 3
        reasons = self._build_reasons(lead, customer, score)
        qualified = score >= self.QUALIFY_THRESHOLD
        report = LeadIntelligenceReport(
            lead_id=lead_id,
            score=score,
            temperature=temperature,
            priority=priority,
            purchase_probability=round(probability, 3),
            expected_deal_value=expected_value,
            qualified=qualified,
            reasons=reasons,
        )
        lead.score = score
        lead.metadata["intelligence"] = report.to_dict()
        self._store.crm_leads.save(lead_id, lead)
        return report

    async def _compute_score(self, lead: CRMLead, customer: CustomerProfile | None) -> float:
        try:
            from applications.auto_marketplace.crm.ai_assistant import ai_sales_assistant

            return await ai_sales_assistant.score_lead(lead, customer)
        except Exception:
            score = 30.0
            if lead.vehicle_id:
                score += 20
            if customer and customer.email:
                score += 15
            return min(score, 100.0)

    @staticmethod
    def _classify_temperature(score: float) -> LeadTemperature:
        if score >= 75:
            return LeadTemperature.HOT
        if score >= 45:
            return LeadTemperature.WARM
        return LeadTemperature.COLD

    @staticmethod
    def _estimate_deal_value(lead: CRMLead, customer: CustomerProfile | None) -> float:
        if lead.vehicle_id:
            vehicle = marketplace_store.catalog_vehicles.get(lead.vehicle_id) or marketplace_store.vehicles.get(lead.vehicle_id)
            if vehicle:
                return float(getattr(vehicle, "price", 25000) or 25000)
        budget = 0.0
        if customer:
            budget = float(customer.preferences.get("budget_max", 0))
        return budget or 25000.0

    @staticmethod
    def _build_reasons(lead: CRMLead, customer: CustomerProfile | None, score: float) -> list[str]:
        reasons: list[str] = []
        if lead.vehicle_id:
            reasons.append("Vehicle interest specified")
        if customer and customer.intent_score > 50:
            reasons.append("High customer intent")
        if lead.source.value in {"referral", "dealer"}:
            reasons.append("High-quality lead source")
        if score >= 75:
            reasons.append("Strong engagement signals")
        return reasons or ["Standard lead profile"]

    async def qualify_lead(self, lead_id: str, *, agent_id: str = "ai-agent") -> LeadIntelligenceReport:
        report = await self.analyze_lead(lead_id)
        if report.qualified:
            lead = self._store.crm_leads.get(lead_id)
            if lead:
                from applications.auto_marketplace.crm.models import CRMLeadStatus

                lead.status = CRMLeadStatus.QUALIFIED
                lead.assigned_agent_id = agent_id
                self._store.crm_leads.save(lead_id, lead)
                customer = self._store.customer_profiles.get(lead.customer_id)
                if customer:
                    await publish(
                        CustomerIntentDetectedEvent(
                            customer_id=customer.customer_id,
                            intent_score=customer.intent_score,
                            intent_label=report.temperature.value,
                        )
                    )
            await publish(
                AISalesLeadQualifiedEvent(
                    lead_id=lead_id,
                    score=report.score,
                    temperature=report.temperature.value,
                )
            )
        return report

    async def score_lead(self, lead_id: str) -> float:
        report = await self.analyze_lead(lead_id)
        return report.score


lead_intelligence_service = LeadIntelligenceService()
