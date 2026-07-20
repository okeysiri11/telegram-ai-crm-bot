# AI Insights — anomaly detection, trends, opportunities, risks.

from __future__ import annotations

import logging
from typing import Any

from events.publisher import publish

from applications.auto_marketplace.business_intelligence.events import (
    InsightGeneratedEvent,
    OpportunityDetectedEvent,
    RiskDetectedEvent,
)
from applications.auto_marketplace.business_intelligence.models import BusinessInsight, InsightType

logger = logging.getLogger(__name__)


class AIInsightsService:
    async def detect_anomalies(self, metrics: dict[str, Any]) -> list[BusinessInsight]:
        insights: list[BusinessInsight] = []
        revenue = metrics.get("revenue", 0)
        if revenue < metrics.get("revenue_target", 1) * 0.5:
            insight = BusinessInsight(
                insight_type=InsightType.ANOMALY,
                title="Revenue below target",
                description=f"Revenue {revenue} is significantly below target.",
                severity="warning",
                metadata={"metric": "revenue", "value": revenue},
            )
            insights.append(insight)
        return insights

    async def analyze_trends(self, time_series: list[dict[str, Any]]) -> list[BusinessInsight]:
        if len(time_series) < 2:
            return []
        first = time_series[0].get("value", 0)
        last = time_series[-1].get("value", 0)
        direction = "up" if last > first else "down"
        insight = BusinessInsight(
            insight_type=InsightType.TREND,
            title=f"Trend moving {direction}",
            description=f"Values changed from {first} to {last}.",
            severity="info",
            metadata={"direction": direction},
        )
        await publish(InsightGeneratedEvent(insight_id=insight.insight_id, insight_type="trend", title=insight.title))
        return [insight]

    async def detect_opportunities(self, data: dict[str, Any]) -> list[BusinessInsight]:
        hot_leads = data.get("hot_leads", 0)
        insights: list[BusinessInsight] = []
        if hot_leads > 5:
            insight = BusinessInsight(
                insight_type=InsightType.OPPORTUNITY,
                title="High-value lead cluster",
                description=f"{hot_leads} hot leads ready for conversion.",
                severity="success",
                metadata={"hot_leads": hot_leads},
            )
            insights.append(insight)
            await publish(
                OpportunityDetectedEvent(insight_id=insight.insight_id, title=insight.title, metadata=insight.metadata)
            )
        return insights

    async def detect_risks(self, data: dict[str, Any]) -> list[BusinessInsight]:
        insights: list[BusinessInsight] = []
        churn_risk = data.get("at_risk_customers", 0)
        if churn_risk > 3:
            insight = BusinessInsight(
                insight_type=InsightType.RISK,
                title="Customer churn risk",
                description=f"{churn_risk} customers showing disengagement signals.",
                severity="high",
                metadata={"at_risk_customers": churn_risk},
            )
            insights.append(insight)
            await publish(RiskDetectedEvent(insight_id=insight.insight_id, title=insight.title, severity="high"))
        return insights

    async def executive_recommendations(self, kpis: dict[str, float]) -> list[BusinessInsight]:
        recs: list[BusinessInsight] = []
        conversion = kpis.get("lead_conversion", 0)
        if conversion < 0.15:
            recs.append(
                BusinessInsight(
                    insight_type=InsightType.RECOMMENDATION,
                    title="Improve lead qualification",
                    description="Lead conversion is below 15%. Focus on AI-assisted qualification.",
                    severity="info",
                )
            )
        try:
            from platform_reasoning import reasoning_engine
            from platform_reasoning.models import ReasoningContext

            result = await reasoning_engine.reason(
                ReasoningContext(request="Executive business recommendations", metadata={"kpis": kpis})
            )
            if hasattr(result, "conclusion") and isinstance(result.conclusion, dict):
                for item in result.conclusion.get("recommendations", [])[:3]:
                    recs.append(
                        BusinessInsight(
                            insight_type=InsightType.RECOMMENDATION,
                            title=str(item.get("title", "AI Recommendation")),
                            description=str(item.get("description", "")),
                        )
                    )
        except Exception:
            logger.debug("reasoning engine unavailable for executive recommendations")
        for r in recs:
            await publish(InsightGeneratedEvent(insight_id=r.insight_id, insight_type="recommendation", title=r.title))
        return recs

    async def predictive_alerts(self, forecasts: dict[str, Any]) -> list[BusinessInsight]:
        alerts: list[BusinessInsight] = []
        if forecasts.get("sales_decline_predicted"):
            alerts.append(
                BusinessInsight(
                    insight_type=InsightType.ALERT,
                    title="Predicted sales decline",
                    description="Forecast indicates potential sales drop in next 30 days.",
                    severity="warning",
                )
            )
        return alerts


ai_insights_service = AIInsightsService()
