# AI integration hooks for agricultural catalog (Platform Core via bridges only).

from __future__ import annotations

import logging
from typing import Any

from applications.agro_marketplace.product_catalog.models import AgriculturalProduct, HarvestRecord

logger = logging.getLogger(__name__)


class CatalogAIIntegration:
    @staticmethod
    async def recommend_products(
        product: AgriculturalProduct,
        candidates: list[AgriculturalProduct],
        *,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        scored: list[tuple[float, AgriculturalProduct]] = []
        for item in candidates:
            if item.product_id == product.product_id:
                continue
            if item.status.value == "archived":
                continue
            score = 0.0
            if item.crop_id and item.crop_id == product.crop_id:
                score += 3.0
            if item.region and item.region.lower() == product.region.lower():
                score += 2.0
            if item.category_id and item.category_id == product.category_id:
                score += 1.5
            if abs(item.price - product.price) < max(product.price * 0.2, 1):
                score += 1.0
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item.to_dict() for _, item in scored[:limit]]

    @staticmethod
    async def assess_quality(harvest: HarvestRecord) -> dict[str, Any]:
        score = 100.0
        if harvest.moisture_pct > 14:
            score -= min(30.0, (harvest.moisture_pct - 14) * 5)
        if harvest.foreign_material_pct > 2:
            score -= min(20.0, harvest.foreign_material_pct * 4)
        if harvest.protein_pct and harvest.protein_pct < 10:
            score -= 10.0
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            await platform_bridge.recommend_products(
                {
                    "hook": "quality_assessment",
                    "harvest_id": harvest.harvest_id,
                    "moisture_pct": harvest.moisture_pct,
                    "protein_pct": harvest.protein_pct,
                }
            )
        except Exception:
            logger.debug("quality assessment bridge unavailable")
        grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "reject"
        return {"quality_score": round(score, 2), "suggested_grade": grade}

    @staticmethod
    async def estimate_demand(product: AgriculturalProduct) -> dict[str, Any]:
        base = max(product.quantity, 1.0)
        demand = base * (1.2 if product.region else 1.0)
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            await platform_bridge.recommend_products(
                {"hook": "demand_estimation", "product_id": product.product_id, "quantity": product.quantity}
            )
        except Exception:
            logger.debug("demand estimation bridge unavailable")
        return {"product_id": product.product_id, "estimated_demand": round(demand, 2), "confidence": 0.6}

    @staticmethod
    async def estimate_price(product: AgriculturalProduct) -> float:
        if product.price > 0:
            return product.price
        base = 100.0
        if product.crop_id:
            base += 20.0
        if product.attributes.get("organic"):
            base *= 1.25
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            result = await platform_bridge.recommend_products(
                {"hook": "price_estimation", "product": product.to_dict()}
            )
            if isinstance(result, dict) and result.get("price"):
                return float(result["price"])
        except Exception:
            logger.debug("price estimation bridge unavailable")
        return round(base, 2)

    @staticmethod
    async def auto_categorize(product: AgriculturalProduct) -> str:
        if product.category_id:
            return product.category_id
        name = product.name.lower()
        if any(x in name for x in ("wheat", "maize", "corn", "rice", "barley")):
            return "grains"
        if any(x in name for x in ("coffee", "tea", "cocoa")):
            return "cash_crops"
        if any(x in name for x in ("tomato", "onion", "potato", "vegetable")):
            return "vegetables"
        if any(x in name for x in ("apple", "mango", "banana", "fruit")):
            return "fruits"
        return "general"

    @staticmethod
    async def detect_duplicates_ai(
        product: AgriculturalProduct,
        candidates: list[AgriculturalProduct],
    ) -> list[str]:
        try:
            from platform_reasoning import reasoning_engine

            session = await reasoning_engine.reason(
                query="Detect duplicate agricultural products",
                context={
                    "product": product.to_dict(),
                    "candidates": [c.to_dict() for c in candidates[:20]],
                },
            )
            if hasattr(session, "to_dict"):
                data = session.to_dict()
                ids = data.get("duplicate_ids") or data.get("conclusion", {}).get("duplicate_ids", [])
                return [str(i) for i in ids]
        except Exception:
            logger.debug("ai duplicate detection fallback")
        return []


catalog_ai = CatalogAIIntegration()
