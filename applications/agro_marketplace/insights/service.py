# Insights and anomaly detection for BI.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.analytics.ai_integration import AnalyticsAIIntegration, analytics_ai
from applications.agro_marketplace.analytics.events import AnomalyDetectedEvent, InsightGeneratedEvent
from applications.agro_marketplace.analytics.models import Anomaly, Insight, InsightKind
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class InsightsService:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: AnalyticsAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or analytics_ai

    async def generate(self, *, metrics: dict | None = None) -> list[Insight]:
        metrics = metrics or {}
        await self._ai.generate_insights({"query": "agro bi", "metrics": metrics})
        opportunities = await self._ai.detect_opportunities(metrics)
        insights: list[Insight] = []
        for opp in opportunities:
            insight = Insight(
                kind=InsightKind.OPPORTUNITY,
                title=str(opp.get("opportunity", "opportunity")).replace("_", " ").title(),
                summary=f"Detected opportunity: {opp.get('opportunity')}",
                score=0.8 if opp.get("priority") == "high" else 0.55,
                domain="marketplace",
                actions=[f"Review {opp.get('opportunity')}"],
                metadata=dict(opp),
            )
            saved = self._store.insights.save(insight.insight_id, insight)
            await publish(
                InsightGeneratedEvent(
                    insight_id=saved.insight_id,
                    kind=saved.kind.value,
                    title=saved.title,
                    score=saved.score,
                )
            )
            insights.append(saved)

        if metrics.get("warehouse_utilization", 0) > 0.85:
            insight = Insight(
                kind=InsightKind.RISK,
                title="High Warehouse Utilization",
                summary="Warehouse capacity is nearing saturation",
                score=0.7,
                domain="warehouse",
                actions=["Open overflow storage", "Prioritize outbound shipments"],
            )
            saved = self._store.insights.save(insight.insight_id, insight)
            await publish(
                InsightGeneratedEvent(
                    insight_id=saved.insight_id,
                    kind=saved.kind.value,
                    title=saved.title,
                    score=saved.score,
                )
            )
            insights.append(saved)
        return insights

    async def detect_anomalies(self, metrics: dict[str, float]) -> list[Anomaly]:
        raw = await self._ai.detect_anomalies(metrics)
        results: list[Anomaly] = []
        for item in raw:
            anomaly = Anomaly(
                metric=item["metric"],
                observed=float(item["observed"]),
                expected=float(item["expected"]),
                severity=item.get("severity", "medium"),
                domain="kpi",
                notes="Automatic anomaly detection",
            )
            saved = self._store.anomalies.save(anomaly.anomaly_id, anomaly)
            await publish(
                AnomalyDetectedEvent(
                    anomaly_id=saved.anomaly_id,
                    metric=saved.metric,
                    severity=saved.severity,
                    observed=saved.observed,
                )
            )
            results.append(saved)
        return results

    def list_insights(self) -> list[Insight]:
        return sorted(self._store.insights.list_all(), key=lambda i: i.created_at, reverse=True)

    def list_anomalies(self) -> list[Anomaly]:
        return sorted(self._store.anomalies.list_all(), key=lambda a: a.created_at, reverse=True)


insights_service = InsightsService()
