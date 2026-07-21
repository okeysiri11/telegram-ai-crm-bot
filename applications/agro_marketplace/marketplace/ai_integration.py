# AI hooks for CRM and trading (Platform Core via bridges only).

from __future__ import annotations

import logging
from typing import Any

from applications.agro_marketplace.marketplace.models import (
    AgriculturalLead,
    BuyerProfile,
    PurchaseRequest,
    SalesOffer,
    SupplierProfile,
)

logger = logging.getLogger(__name__)


class TradingAIIntegration:
    @staticmethod
    def score_lead(lead: AgriculturalLead) -> float:
        score = 40.0
        if lead.email:
            score += 10
        if lead.crop_interest:
            score += 15
        if lead.region:
            score += 10
        if lead.source in {"referral", "rfq", "marketplace"}:
            score += 15
        if lead.role in {"buyer", "exporter"}:
            score += 10
        return min(100.0, score)

    @staticmethod
    async def recommend_buyers(
        offer: SalesOffer,
        buyers: list[BuyerProfile],
        *,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        scored: list[tuple[float, BuyerProfile]] = []
        for buyer in buyers:
            score = 0.0
            if offer.crop_id and offer.crop_id in buyer.preferred_crops:
                score += 4.0
            if buyer.budget_max <= 0 or offer.price * offer.quantity <= buyer.budget_max:
                score += 2.0
            if buyer.country:
                score += 0.5
            if score > 0:
                scored.append((score + buyer.score / 100, buyer))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [b.to_dict() | {"match_score": round(s, 2)} for s, b in scored[:limit]]

    @staticmethod
    async def recommend_suppliers(
        request: PurchaseRequest,
        suppliers: list[SupplierProfile],
        *,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        scored: list[tuple[float, SupplierProfile]] = []
        for supplier in suppliers:
            score = 0.0
            if request.crop_id and request.crop_id in supplier.products:
                score += 4.0
            if request.crop_id and request.crop_id in " ".join(supplier.products):
                score += 2.0
            score += supplier.score / 50
            if score > 0:
                scored.append((score, supplier))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s.to_dict() | {"match_score": round(sc, 2)} for sc, s in scored[:limit]]

    @staticmethod
    def match_score(offer: SalesOffer, request: PurchaseRequest) -> float:
        score = 0.0
        if offer.crop_id and offer.crop_id == request.crop_id:
            score += 40
        if offer.product_id and offer.product_id == request.product_id:
            score += 25
        if offer.region and request.region and offer.region.lower() == request.region.lower():
            score += 15
        if request.max_price <= 0 or offer.price <= request.max_price:
            score += 15
        if offer.quantity >= request.quantity > 0:
            score += 10
        elif request.quantity > 0 and offer.quantity > 0:
            score += 5 * min(1.0, offer.quantity / request.quantity)
        return round(min(100.0, score), 2)

    @staticmethod
    async def suggest_negotiation(
        *,
        current_price: float,
        current_quantity: float,
        target_price: float = 0.0,
        target_quantity: float = 0.0,
    ) -> dict[str, Any]:
        suggested_price = current_price
        if target_price > 0:
            suggested_price = round((current_price + target_price) / 2, 2)
        suggested_qty = current_quantity
        if target_quantity > 0:
            suggested_qty = round((current_quantity + target_quantity) / 2, 2)
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            await platform_bridge.recommend_products(
                {
                    "hook": "negotiation_assistant",
                    "current_price": current_price,
                    "target_price": target_price,
                }
            )
        except Exception:
            logger.debug("negotiation assistant bridge unavailable")
        return {
            "suggested_price": suggested_price,
            "suggested_quantity": suggested_qty,
            "rationale": "midpoint between current and target terms",
        }

    @staticmethod
    async def recommend_price(offer: SalesOffer, market_avg: float = 0.0) -> dict[str, Any]:
        base = offer.price or market_avg or 100.0
        recommended = round(base * 0.98 if market_avg and offer.price > market_avg else base, 2)
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            await platform_bridge.recommend_products(
                {"hook": "price_recommendation", "offer": offer.to_dict(), "market_avg": market_avg}
            )
        except Exception:
            logger.debug("price recommendation bridge unavailable")
        return {"recommended_price": recommended, "market_avg": market_avg}

    @staticmethod
    def detect_opportunities(
        offers: list[SalesOffer],
        requests: list[PurchaseRequest],
        *,
        min_score: float = 50.0,
    ) -> list[dict[str, Any]]:
        opportunities: list[dict[str, Any]] = []
        for offer in offers:
            if offer.status.value not in {"published", "matched", "negotiating"}:
                continue
            for request in requests:
                if request.status != "open":
                    continue
                score = TradingAIIntegration.match_score(offer, request)
                if score >= min_score:
                    opportunities.append(
                        {
                            "offer_id": offer.offer_id,
                            "request_id": request.request_id,
                            "score": score,
                            "buyer_id": request.buyer_id,
                            "seller_id": offer.seller_id,
                        }
                    )
        opportunities.sort(key=lambda x: x["score"], reverse=True)
        return opportunities


trading_ai = TradingAIIntegration()
