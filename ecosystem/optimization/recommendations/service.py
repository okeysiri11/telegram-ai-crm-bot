# Recommendation engine — optimization, architecture, cost, scaling advice.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from ecosystem.optimization.events import RecommendationGeneratedEvent
from ecosystem.optimization.models import Recommendation, RecommendationCategory
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class RecommendationEngine:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    async def generate(self, *, force: bool = False) -> list[Recommendation]:
        existing = self._store.recommendations.list_all()
        if existing and not force:
            open_ones = [r for r in existing if r.status == "open"]
            if open_ones:
                return sorted(open_ones, key=lambda r: r.priority)

        from ecosystem.optimization.continuous_learning.service import continuous_learning
        from ecosystem.optimization.benchmark.service import benchmark_service

        analysis = continuous_learning.analyze_history()
        benchmarks = benchmark_service.run_suite()
        recommendations: list[Recommendation] = []

        if analysis["success_rate"] < 0.95:
            recommendations.append(
                await self._create(
                    RecommendationCategory.WORKFLOW,
                    "Improve workflow reliability",
                    "Success rate is below target; add retries and clearer escalation paths.",
                    priority=20,
                    impact="high",
                    estimated_gain=0.1,
                    actions=["Enable retry policies", "Review dead-letter queue", "Tighten specialist routing"],
                )
            )

        latency_bench = next((b for b in benchmarks if b.name == "avg_latency_ms"), None)
        if latency_bench and latency_bench.score > latency_bench.baseline:
            recommendations.append(
                await self._create(
                    RecommendationCategory.OPTIMIZATION,
                    "Reduce response latency",
                    "Average latency exceeds baseline; optimize hot paths and cache knowledge lookups.",
                    priority=25,
                    impact="high",
                    estimated_gain=0.15,
                    actions=["Cache knowledge search", "Parallelize agent collaboration", "Trim prompt context"],
                )
            )

        util = next((b for b in benchmarks if b.name == "agent_utilization"), None)
        if util and util.score > 0.8:
            recommendations.append(
                await self._create(
                    RecommendationCategory.RESOURCE,
                    "Rebalance agent workload",
                    "Agent utilization is high; redistribute tasks across departments.",
                    priority=30,
                    impact="medium",
                    estimated_gain=0.12,
                    actions=["Run workforce balance", "Scale specialist pool", "Defer low-priority work"],
                )
            )
        elif util and util.score < 0.3:
            recommendations.append(
                await self._create(
                    RecommendationCategory.COST,
                    "Reduce idle agent cost",
                    "Agent utilization is low; consolidate capacity or expand workload intake.",
                    priority=40,
                    impact="medium",
                    estimated_gain=0.08,
                    actions=["Consolidate underused specialists", "Increase inbound automation"],
                )
            )

        recommendations.append(
            await self._create(
                RecommendationCategory.ARCHITECTURE,
                "Strengthen learning feedback loops",
                "Wire continuous learning insights into executive planning and knowledge graph.",
                priority=35,
                impact="medium",
                estimated_gain=0.1,
                actions=["Schedule weekly learning cycles", "Publish insights to knowledge graph"],
            )
        )

        recommendations.append(
            await self._create(
                RecommendationCategory.SCALING,
                "Plan capacity for growth",
                "Run capacity simulations before major campaign or marketplace spikes.",
                priority=45,
                impact="high",
                estimated_gain=0.2,
                actions=["Run capacity simulation", "Pre-scale inventory specialists", "Alert executives on headroom < 20%"],
            )
        )

        return sorted(recommendations, key=lambda r: r.priority)

    async def _create(
        self,
        category: RecommendationCategory,
        title: str,
        description: str,
        *,
        priority: int,
        impact: str,
        estimated_gain: float,
        actions: list[str],
    ) -> Recommendation:
        rec = Recommendation(
            category=category,
            title=title,
            description=description,
            priority=priority,
            impact=impact,
            estimated_gain=estimated_gain,
            actions=actions,
        )
        self._store.recommendations.save(rec.recommendation_id, rec)
        await publish(
            RecommendationGeneratedEvent(
                recommendation_id=rec.recommendation_id,
                category=category.value,
                title=title,
                priority=priority,
            )
        )
        return rec

    def list_recommendations(self, *, category: RecommendationCategory | None = None) -> list[Recommendation]:
        recs = self._store.recommendations.list_all()
        if category:
            recs = [r for r in recs if r.category == category]
        return sorted(recs, key=lambda r: r.priority)

    def accept(self, recommendation_id: str) -> Recommendation:
        from ecosystem.shared.exceptions import NotFoundError

        rec = self._store.recommendations.get(recommendation_id)
        if rec is None:
            raise NotFoundError("Recommendation", recommendation_id)
        rec.status = "accepted"
        self._store.recommendations.save(recommendation_id, rec)
        return rec


recommendation_engine = RecommendationEngine()
