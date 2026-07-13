# Cross Posting v1 — product layer.

from __future__ import annotations

import uuid
from typing import Any

from database.session import get_session
from repositories.cross_posting_repository import PostingJobRepository, PostingResultRepository
from services.pg_cross_posting_engine import CrossPostingEngineError, CrossPostingEngineV1

CROSS_POSTING_FEATURES = frozenset({
    "scheduled_posting",
    "reposting",
    "publication_tracking",
    "duplicate_detection",
    "post_analytics_collection",
})


class CrossPostingProductError(Exception):
    pass


class CrossPostingV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await CrossPostingEngineV1.user_can_access(user_id)

    @staticmethod
    def list_features() -> list[dict[str, str]]:
        labels = {
            "scheduled_posting": "Scheduled Posting",
            "reposting": "Reposting",
            "publication_tracking": "Publication Tracking",
            "duplicate_detection": "Duplicate Detection",
            "post_analytics_collection": "Post Analytics Collection",
        }
        return [{"code": k, "label": labels[k]} for k in sorted(CROSS_POSTING_FEATURES)]

    @staticmethod
    async def _wrap(coro):
        try:
            return await coro
        except CrossPostingEngineError as exc:
            raise CrossPostingProductError(str(exc)) from exc

    @staticmethod
    async def get_engine(actor_id: int, tenant_id: uuid.UUID) -> dict[str, Any]:
        dashboard = await CrossPostingV1._wrap(
            CrossPostingEngineV1.get_cross_posting_dashboard(actor_id, tenant_id)
        )
        return {**dashboard, "features": list(CROSS_POSTING_FEATURES)}

    @staticmethod
    async def get_feature(
        actor_id: int,
        tenant_id: uuid.UUID,
        feature: str,
        *,
        job_id: uuid.UUID | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        if feature not in CROSS_POSTING_FEATURES:
            raise CrossPostingProductError(f"Unknown feature: {feature}")

        if feature == "duplicate_detection":
            sample = content or "Sample vehicle listing post"
            result = await CrossPostingV1._wrap(
                CrossPostingEngineV1.check_duplicate(tenant_id, sample)
            )
            return {"feature": feature, **result}

        if feature == "publication_tracking":
            if not job_id:
                async with get_session() as session:
                    jobs = await PostingJobRepository(session).list_by_tenant(tenant_id, limit=1)
                if not jobs:
                    return {"feature": feature, "message": "No jobs available"}
                job_id = jobs[0].id
            result = await CrossPostingV1._wrap(
                CrossPostingEngineV1.get_publication_tracking(actor_id, tenant_id, job_id)
            )
            return {"feature": feature, **result}

        if feature == "post_analytics_collection":
            async with get_session() as session:
                results = await PostingResultRepository(session).list_by_tenant(tenant_id, limit=1)
            if not results:
                return {"feature": feature, "message": "No published results yet"}
            result = await CrossPostingV1._wrap(
                CrossPostingEngineV1.collect_post_analytics(
                    actor_id, tenant_id, results[0].id
                )
            )
            return {"feature": feature, "analytics": result}

        return {"feature": feature, "status": "available", "description": feature.replace("_", " ")}
