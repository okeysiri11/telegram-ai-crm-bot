# Strategy layer — convert learning & recommendations into strategic updates.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from ecosystem.optimization.events import StrategyUpdatedEvent
from ecosystem.optimization.models import StrategyUpdate
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class StrategyService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    async def update_from_recommendations(
        self,
        title: str,
        *,
        focus: str = "ecosystem_optimization",
        recommendation_ids: list[str] | None = None,
    ) -> StrategyUpdate:
        recs = self._store.recommendations.list_all()
        if recommendation_ids:
            recs = [r for r in recs if r.recommendation_id in recommendation_ids]
        else:
            recs = [r for r in recs if r.status == "open"][:5]

        strategy = StrategyUpdate(
            title=title,
            focus=focus,
            objectives=[r.title for r in recs],
            recommendations=[r.recommendation_id for r in recs],
        )
        self._store.strategy_updates.save(strategy.strategy_id, strategy)
        await publish(
            StrategyUpdatedEvent(
                strategy_id=strategy.strategy_id,
                title=title,
                focus=focus,
            )
        )

        # Integrate with executive / planning when available
        try:
            from ecosystem.workforce.models import PlanHorizon
            from ecosystem.workforce.planning.service import planning_service

            await planning_service.create_plan(
                f"Strategy: {title}",
                PlanHorizon.QUARTERLY,
                [{"recommendation_id": r.recommendation_id, "title": r.title} for r in recs],
            )
        except Exception:
            pass

        return strategy

    def list_strategies(self) -> list[StrategyUpdate]:
        return sorted(self._store.strategy_updates.list_all(), key=lambda s: s.created_at, reverse=True)

    def latest(self) -> StrategyUpdate | None:
        strategies = self.list_strategies()
        return strategies[0] if strategies else None


strategy_service = StrategyService()
