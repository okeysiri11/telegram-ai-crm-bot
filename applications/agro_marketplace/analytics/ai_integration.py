# Analytics AI hooks — Executive AI, Workforce, Knowledge Graph via bridges only.

from __future__ import annotations

import logging
from typing import Any

from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.agro_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge

logger = logging.getLogger(__name__)


class AnalyticsAIIntegration:
    def __init__(
        self,
        platform: PlatformBridge | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self._platform = platform or platform_bridge
        self._ecosystem = ecosystem or ecosystem_bridge

    async def executive_report(self, topic: str, metrics: dict[str, Any]) -> dict[str, Any]:
        brief = await self._ecosystem.executive_brief(topic, metrics=metrics)
        await self._platform.start_ai_workflow("executive_report", {"topic": topic, "metrics": metrics})
        return brief if isinstance(brief, dict) else {"topic": topic, "brief": brief}

    async def generate_insights(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        await self._ecosystem.invoke_workforce("analytics_insights", context=context)
        knowledge = self._ecosystem.knowledge_lookup(context.get("query", "agro marketplace trends"))
        return [
            {
                "source": "workforce",
                "knowledge_hits": len(knowledge),
                "context_keys": list(context.keys()),
            }
        ]

    async def detect_anomalies(self, metrics: dict[str, float]) -> list[dict[str, Any]]:
        anomalies = []
        for name, value in metrics.items():
            expected = abs(value) * 0.85 if value else 1.0
            if value > 0 and abs(value - expected) / max(expected, 1e-6) > 0.35:
                anomalies.append(
                    {
                        "metric": name,
                        "observed": value,
                        "expected": round(expected, 2),
                        "severity": "high" if value > expected * 1.5 else "medium",
                    }
                )
        await self._platform.start_ai_workflow("anomaly_detection", {"count": len(anomalies)})
        return anomalies

    async def predict_risks(self, domain: str, signals: dict[str, Any]) -> dict[str, Any]:
        self._ecosystem.check_governance("analytics_risk", {"domain": domain, **signals})
        score = min(1.0, 0.2 + 0.1 * len(signals))
        if signals.get("warehouse_utilization", 0) > 0.9:
            score += 0.25
        if signals.get("export_at_risk", 0) > 0:
            score += 0.2
        return {"domain": domain, "risk_score": round(min(1.0, score), 2), "signals": signals}

    async def detect_opportunities(self, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        opps = []
        if metrics.get("buyer_conversion", 0) < 0.3 and metrics.get("order_volume", 0) > 0:
            opps.append({"opportunity": "improve_buyer_conversion", "priority": "high"})
        if metrics.get("export_volume", 0) > 0:
            opps.append({"opportunity": "expand_export_corridors", "priority": "medium"})
        if metrics.get("inventory_turnover", 0) < 1.0:
            opps.append({"opportunity": "accelerate_inventory_movement", "priority": "medium"})
        knowledge = self._ecosystem.knowledge_lookup("trade opportunities agriculture")
        return opps or [{"opportunity": "grow_marketplace_listings", "knowledge_hits": len(knowledge)}]

    async def optimize_recommendations(self, focus: str, metrics: dict[str, Any]) -> list[str]:
        await self._ecosystem.invoke_workforce(
            "optimization_recommendations",
            context={"focus": focus, "metrics": metrics},
        )
        recs = [f"Optimize {focus} using current KPIs"]
        if metrics.get("warehouse_utilization", 0) > 0.85:
            recs.append("Rebalance warehouse capacity across regions")
        if metrics.get("gross_margin", 0) < 0.2:
            recs.append("Review pricing and supplier costs")
        return recs

    async def run_scenario(self, name: str, inputs: dict[str, Any]) -> dict[str, Any]:
        await self._platform.start_ai_workflow("scenario_simulation", {"name": name, "inputs": inputs})
        price_shock = float(inputs.get("price_change_pct", 0)) / 100.0
        demand_shock = float(inputs.get("demand_change_pct", 0)) / 100.0
        base_revenue = float(inputs.get("base_revenue", 10000))
        projected = base_revenue * (1 + price_shock) * (1 + demand_shock)
        return {
            "name": name,
            "projected_revenue": round(projected, 2),
            "delta": round(projected - base_revenue, 2),
            "inputs": inputs,
        }


analytics_ai = AnalyticsAIIntegration()
