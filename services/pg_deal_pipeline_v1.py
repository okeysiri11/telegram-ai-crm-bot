# Deal Pipeline v1 — product layer over Deal Pipeline Engine v2.

from __future__ import annotations

import uuid
from typing import Any

from database.models.deal_pipeline_engine import DealPipelineStageCode
from services.pg_deal_pipeline_engine import DealPipelineEngineError, DealPipelineEngineV2

PIPELINE_FEATURES = frozenset({
    "stage_transition_validation",
    "automatic_task_creation",
    "manager_assignment",
    "sla_timers",
    "overdue_detection",
})


class DealPipelineProductError(Exception):
    pass


class DealPipelineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await DealPipelineEngineV2.user_can_access(user_id)

    @staticmethod
    def list_features() -> list[dict[str, str]]:
        labels = {
            "stage_transition_validation": "Stage Transition Validation",
            "automatic_task_creation": "Automatic Task Creation",
            "manager_assignment": "Manager Assignment",
            "sla_timers": "SLA Timers",
            "overdue_detection": "Overdue Detection",
        }
        return [{"code": k, "label": labels[k]} for k in sorted(PIPELINE_FEATURES)]

    @staticmethod
    async def _wrap(coro):
        try:
            return await coro
        except DealPipelineEngineError as exc:
            raise DealPipelineProductError(str(exc)) from exc

    @staticmethod
    async def get_pipeline(actor_id: int, tenant_id: uuid.UUID) -> dict[str, Any]:
        dashboard = await DealPipelineV1._wrap(
            DealPipelineEngineV2.get_pipeline_dashboard(actor_id, tenant_id)
        )
        return {
            **dashboard,
            "features": list(PIPELINE_FEATURES),
        }

    @staticmethod
    async def get_feature(
        actor_id: int,
        tenant_id: uuid.UUID,
        feature: str,
        *,
        deal_id: uuid.UUID | None = None,
        from_stage: str | None = None,
        to_stage: str | None = None,
    ) -> dict[str, Any]:
        if feature not in PIPELINE_FEATURES:
            raise DealPipelineProductError(f"Unknown feature: {feature}")

        if feature == "stage_transition_validation":
            if not from_stage or not to_stage:
                from_stage = from_stage or DealPipelineStageCode.NEW_LEAD.value
                to_stage = to_stage or DealPipelineStageCode.CONTACTED.value
            result = await DealPipelineV1._wrap(
                DealPipelineEngineV2.validate_stage_transition(tenant_id, from_stage, to_stage)
            )
            return {"feature": feature, **result}

        if feature == "overdue_detection":
            result = await DealPipelineV1._wrap(
                DealPipelineEngineV2.detect_overdue(actor_id, tenant_id)
            )
            return {"feature": feature, **result}

        if feature == "manager_assignment":
            deals = await DealPipelineV1._wrap(
                DealPipelineEngineV2.list_deals(actor_id, tenant_id, limit=5)
            )
            return {
                "feature": feature,
                "status": "available",
                "recent_deals": deals,
                "description": "Assign managers via assign_manager API or engine method",
            }

        if feature == "automatic_task_creation":
            if deal_id:
                detail = await DealPipelineV1._wrap(
                    DealPipelineEngineV2.get_deal(actor_id, tenant_id, deal_id)
                )
                auto_tasks = [t for t in detail["tasks"] if t.get("auto_created")]
                return {"feature": feature, "deal_id": str(deal_id), "auto_tasks": auto_tasks}

            deals = await DealPipelineV1._wrap(
                DealPipelineEngineV2.list_deals(actor_id, tenant_id, limit=1)
            )
            if not deals:
                return {"feature": feature, "message": "No deals yet — create one to see auto tasks"}
            deal_id = uuid.UUID(deals[0]["id"])
            detail = await DealPipelineV1._wrap(
                DealPipelineEngineV2.get_deal(actor_id, tenant_id, deal_id)
            )
            auto_tasks = [t for t in detail["tasks"] if t.get("auto_created")]
            return {"feature": feature, "deal_id": str(deal_id), "auto_tasks": auto_tasks}

        if feature == "sla_timers":
            deals = await DealPipelineV1._wrap(
                DealPipelineEngineV2.list_deals(actor_id, tenant_id, limit=20)
            )
            with_sla = [
                {"id": d["id"], "title": d["title"], "sla_due_at": d["sla_due_at"]}
                for d in deals
                if d.get("sla_due_at")
            ]
            return {"feature": feature, "deals_with_sla": with_sla, "count": len(with_sla)}

        return {"feature": feature, "status": "available"}
