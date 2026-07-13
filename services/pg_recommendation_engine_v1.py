# Recommendation Engine v1 — product layer over recommendation engine.

from __future__ import annotations

import uuid
from typing import Any

from database.models.recommendation_engine import RecommendationType
from services.pg_recommendation_engine import RecommendationEngineError, RecommendationEngineV1

RECOMMENDATION_FEATURES = frozenset({
    "vehicle_recommendation",
    "customer_similarity_matching",
    "upsell_opportunities",
    "cross_sell_opportunities",
    "financing_recommendation",
})


class RecommendationProductError(Exception):
    pass


class RecommendationEngineV1Product:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await RecommendationEngineV1.user_can_access(user_id)

    @staticmethod
    def list_features() -> list[dict[str, str]]:
        labels = {
            "vehicle_recommendation": "Vehicle Recommendation",
            "customer_similarity_matching": "Customer Similarity Matching",
            "upsell_opportunities": "Upsell Opportunities",
            "cross_sell_opportunities": "Cross-sell Opportunities",
            "financing_recommendation": "Financing Recommendation",
        }
        return [{"code": k, "label": labels[k]} for k in sorted(RECOMMENDATION_FEATURES)]

    @staticmethod
    async def _wrap(coro):
        try:
            return await coro
        except RecommendationEngineError as exc:
            raise RecommendationProductError(str(exc)) from exc

    @staticmethod
    async def get_engine(actor_id: int, tenant_id: uuid.UUID) -> dict[str, Any]:
        dashboard = await RecommendationEngineV1Product._wrap(
            RecommendationEngineV1.get_engine_dashboard(actor_id, tenant_id)
        )
        profiles = await RecommendationEngineV1.list_profiles(actor_id, tenant_id, limit=10)
        return {
            **dashboard,
            "features": list(RECOMMENDATION_FEATURES),
            "recent_profiles": profiles,
        }

    @staticmethod
    async def get_feature(
        actor_id: int,
        tenant_id: uuid.UUID,
        feature: str,
        *,
        profile_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        if feature not in RECOMMENDATION_FEATURES:
            raise RecommendationProductError(f"Unknown feature: {feature}")
        if profile_id is None:
            profiles = await RecommendationEngineV1.list_profiles(actor_id, tenant_id, limit=1)
            if not profiles:
                return {"feature": feature, "message": "No profiles available — create one first"}
            profile_id = uuid.UUID(profiles[0]["id"])

        getters = {
            "vehicle_recommendation": lambda: RecommendationEngineV1.recommend_vehicles(
                actor_id, tenant_id, profile_id
            ),
            "customer_similarity_matching": lambda: RecommendationEngineV1.match_similar_customers(
                actor_id, tenant_id, profile_id
            ),
            "upsell_opportunities": lambda: RecommendationEngineV1.find_upsell_opportunities(
                actor_id, tenant_id, profile_id
            ),
            "cross_sell_opportunities": lambda: RecommendationEngineV1.find_cross_sell_opportunities(
                actor_id, tenant_id, profile_id
            ),
            "financing_recommendation": lambda: RecommendationEngineV1.recommend_financing(
                actor_id, tenant_id, profile_id
            ),
        }
        result = await RecommendationEngineV1Product._wrap(getters[feature]())
        return {"feature": feature, **result}
