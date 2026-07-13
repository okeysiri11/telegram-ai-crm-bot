# AI Procurement Agent v1 — product layer over procurement engine.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from services.pg_ai_procurement_agent_engine import (
    AiProcurementAgentError,
    AiProcurementAgentV1,
)

PROCUREMENT_FEATURES = frozenset({
    "market_analysis",
    "roi_prediction",
    "repair_estimation",
    "sale_price_prediction",
    "supplier_scoring",
})


class ProcurementAgentError(Exception):
    pass


class ProcurementAgentV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await AiProcurementAgentV1.user_can_access(user_id)

    @staticmethod
    def list_features() -> list[dict[str, str]]:
        labels = {
            "market_analysis": "Market Analysis",
            "roi_prediction": "ROI Prediction",
            "repair_estimation": "Repair Estimation",
            "sale_price_prediction": "Sale Price Prediction",
            "supplier_scoring": "Supplier Scoring",
        }
        return [{"code": k, "label": labels[k]} for k in sorted(PROCUREMENT_FEATURES)]

    @staticmethod
    async def _wrap(coro):
        try:
            return await coro
        except AiProcurementAgentError as exc:
            raise ProcurementAgentError(str(exc)) from exc

    @staticmethod
    async def get_agent(actor_id: int) -> dict[str, Any]:
        if not await ProcurementAgentV1.user_can_access(actor_id):
            raise ProcurementAgentError("Procurement agent access denied")

        return {
            "features": list(PROCUREMENT_FEATURES),
            "summary": {
                "active_lots": (await ProcurementAgentV1.get_market_analysis_module(actor_id)).get(
                    "active_lots", 0
                ),
                "open_opportunities": len(
                    await AiProcurementAgentV1.list_opportunities(actor_id, limit=100)
                ),
                "suppliers_scored": (
                    await ProcurementAgentV1.get_supplier_scoring_module(actor_id)
                ).get("count", 0),
            },
            "feature_data": {
                "market_analysis": await ProcurementAgentV1.get_market_analysis_module(actor_id),
                "roi_prediction": await ProcurementAgentV1.get_roi_prediction_module(actor_id),
                "repair_estimation": await ProcurementAgentV1.get_repair_estimation_module(actor_id),
                "sale_price_prediction": await ProcurementAgentV1.get_sale_price_prediction_module(
                    actor_id
                ),
                "supplier_scoring": await ProcurementAgentV1.get_supplier_scoring_module(actor_id),
            },
        }

    @staticmethod
    async def get_feature(actor_id: int, feature: str) -> dict[str, Any]:
        if feature not in PROCUREMENT_FEATURES:
            raise ProcurementAgentError(f"Unknown feature: {feature}")
        return await {
            "market_analysis": ProcurementAgentV1.get_market_analysis_module,
            "roi_prediction": ProcurementAgentV1.get_roi_prediction_module,
            "repair_estimation": ProcurementAgentV1.get_repair_estimation_module,
            "sale_price_prediction": ProcurementAgentV1.get_sale_price_prediction_module,
            "supplier_scoring": ProcurementAgentV1.get_supplier_scoring_module,
        }[feature](actor_id)

    @staticmethod
    async def get_market_analysis_module(
        actor_id: int,
        *,
        make: str | None = None,
        model: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        analysis = await AiProcurementAgentV1.analyze_market(
            actor_id, make=make, model=model, source=source
        )
        return {
            "feature": "market_analysis",
            "analysis": analysis,
            "active_lots": analysis["result"].get("active_lots", 0),
            "by_source": analysis["result"].get("by_source", {}),
        }

    @staticmethod
    async def get_roi_prediction_module(actor_id: int) -> dict[str, Any]:
        opportunities = await AiProcurementAgentV1.list_opportunities(actor_id, limit=10)
        predictions: list[dict[str, Any]] = []
        for opp in opportunities[:5]:
            lot_id = opp.get("auction_lot_id")
            if not lot_id:
                continue
            try:
                roi = await AiProcurementAgentV1.estimate_roi(
                    actor_id,
                    acquisition_price=Decimal(opp["acquisition_price"]),
                    auction_lot_id=uuid.UUID(lot_id),
                )
                predictions.append({"opportunity_id": opp["id"], "roi_analysis": roi})
            except AiProcurementAgentError:
                continue
        return {
            "feature": "roi_prediction",
            "opportunities": opportunities,
            "predictions": predictions,
        }

    @staticmethod
    async def get_repair_estimation_module(actor_id: int) -> dict[str, Any]:
        analyses = await AiProcurementAgentV1.list_analyses(
            actor_id, analysis_type="REPAIR_ESTIMATE", limit=10
        )
        return {
            "feature": "repair_estimation",
            "recent_estimates": analyses,
        }

    @staticmethod
    async def get_sale_price_prediction_module(actor_id: int) -> dict[str, Any]:
        analyses = await AiProcurementAgentV1.list_analyses(
            actor_id, analysis_type="SALE_PRICE_ESTIMATE", limit=10
        )
        return {
            "feature": "sale_price_prediction",
            "recent_predictions": analyses,
        }

    @staticmethod
    async def get_supplier_scoring_module(
        actor_id: int,
        *,
        source: str | None = None,
    ) -> dict[str, Any]:
        scoring = await AiProcurementAgentV1.score_suppliers(actor_id, source=source)
        return {"feature": "supplier_scoring", **scoring}

    @staticmethod
    async def predict_roi(actor_id: int, **kwargs: Any) -> dict[str, Any]:
        return await ProcurementAgentV1._wrap(AiProcurementAgentV1.estimate_roi(actor_id, **kwargs))

    @staticmethod
    async def estimate_repair(actor_id: int, **kwargs: Any) -> dict[str, Any]:
        return await ProcurementAgentV1._wrap(
            AiProcurementAgentV1.estimate_repair_costs(actor_id, **kwargs)
        )

    @staticmethod
    async def predict_sale_price(actor_id: int, **kwargs: Any) -> dict[str, Any]:
        return await ProcurementAgentV1._wrap(
            AiProcurementAgentV1.estimate_final_sale_price(actor_id, **kwargs)
        )
