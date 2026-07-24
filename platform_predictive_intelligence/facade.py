"""Predictive Intelligence library facade — Sprint 24.3."""

from __future__ import annotations

from typing import Any

from platform_predictive_intelligence.business import BusinessForecastEngine
from platform_predictive_intelligence.confidence import ConfidenceScore
from platform_predictive_intelligence.customer import CustomerPredictionEngine
from platform_predictive_intelligence.dashboard import OwnerDashboard
from platform_predictive_intelligence.integrations import PredictiveIntegrations
from platform_predictive_intelligence.learning import ContinuousLearning
from platform_predictive_intelligence.marketing import MarketingPrediction
from platform_predictive_intelligence.models import FORECAST_DOMAINS, PRINCIPLES
from platform_predictive_intelligence.operations import OperationsPrediction
from platform_predictive_intelligence.opportunity import OpportunityDetector
from platform_predictive_intelligence.registry import PredictionRegistry
from platform_predictive_intelligence.risk import RiskIntelligence
from platform_predictive_intelligence.scenarios import AIScenarioGenerator


class PredictiveIntelligenceLibrary:
    def __init__(self) -> None:
        self.registry = PredictionRegistry()
        self.business = BusinessForecastEngine()
        self.customer = CustomerPredictionEngine()
        self.marketing = MarketingPrediction()
        self.operations = OperationsPrediction()
        self.risk = RiskIntelligence()
        self.opportunity = OpportunityDetector()
        self.scenarios = AIScenarioGenerator()
        self.confidence = ConfidenceScore()
        self.learning = ContinuousLearning()
        self.dashboard = OwnerDashboard()
        self.integrations = PredictiveIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        for domain in FORECAST_DOMAINS:
            self.registry.register(
                model_id=f"m_{domain}",
                domain=domain,
                prediction_type="business_forecast",
                data_sources=["commerce_core", "crm"],
                accuracy=0.82,
            )
        self.registry.register(model_id="m_customer", domain="customer", prediction_type="customer", data_sources=["crm"], accuracy=0.78)
        self.registry.register(model_id="m_marketing", domain="marketing", prediction_type="marketing", data_sources=["ai_marketing_os"], accuracy=0.8)
        self.registry.register(model_id="m_ops", domain="operations", prediction_type="operations", data_sources=["operations_center"], accuracy=0.77)
        self.registry.register(model_id="m_risk", domain="risk", prediction_type="risk", data_sources=["enterprise_knowledge_graph"], accuracy=0.75)

        biz = self.confidence.attach(
            prediction=self.business.forecast(domain="revenue", horizon_days=30, baseline=10000),
            confidence=0.81,
            data_used=["commerce_core", "crm"],
        )
        cust = self.confidence.attach(
            prediction=self.customer.predict(customer_id="c1", signals={"days_since_visit": 45, "visits": 4, "spend": 300}),
            confidence=0.76,
            data_used=["crm"],
        )
        mkt = self.confidence.attach(prediction=self.marketing.predict(campaign_id="camp1", channel="whatsapp", budget=200), confidence=0.79)
        ops = self.confidence.attach(prediction=self.operations.predict(branch_id="b1", load_pct=0.88, inventory_days=5), confidence=0.74)
        risks = self.risk.assess(signals={"customer_loss": 0.55, "operational": 0.5})
        opps = self.opportunity.detect(signals={"open_slots": 8, "promo_headroom": 1, "underused_service": "coloring"})
        scenarios = self.scenarios.generate(baseline=biz["forecast_value"], domain="revenue")
        learned = self.learning.compare(forecast=10000, actual=9800, confirmed=True, model_id="m_revenue")
        self.registry.record_training("m_revenue", note="confirmed_actual", accuracy=learned["accuracy"])
        dash = self.dashboard.render(
            forecasts=[biz],
            risks=risks,
            opportunities=opps,
            recommendations=["rebook_at_risk_clients", "restock_materials", "shift_staff_to_peak"],
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "predictive_intelligence_ready": True,
            "business_forecast_ready": True,
            "risk_intelligence_ready": True,
            "opportunity_detector_ready": True,
            "models_registered": len(self.registry.list_models()),
            "explained": biz["explained"],
            "scenarios_ready": len(scenarios["scenarios"]) == 4,
            "learned_confirmed": learned["learned"],
            "ai_may_act": False,
            "auto_actions": False,
            "shared_prediction_layer": True,
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "business": biz,
                "customer": cust,
                "marketing": mkt,
                "operations": ops,
                "risks": risks,
                "opportunities": opps,
                "scenarios": scenarios,
                "learning": learned,
                "dashboard": dash,
                "models": self.registry.list_models(),
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "registry",
                "business",
                "customer",
                "marketing",
                "operations",
                "risk",
                "opportunity",
                "scenarios",
                "confidence",
                "learning",
                "dashboard",
            ],
            "principles": self.principles(),
            "models": len(self.registry.list_models()),
        }


predictive_intelligence_library = PredictiveIntelligenceLibrary()
