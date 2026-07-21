# Recommendation engine — products, buyers, suppliers, contracts, inventory/warehouse.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from applications.agro_marketplace.ai.events import RecommendationGeneratedEvent, TradeOpportunityDetectedEvent
from applications.agro_marketplace.ai.models import Recommendation
from applications.agro_marketplace.marketplace.ai_integration import TradingAIIntegration, trading_ai
from applications.agro_marketplace.product_catalog.models import AvailabilityStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class RecommendationEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        trading_ai_svc: TradingAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._trading_ai = trading_ai_svc or trading_ai

    async def _save(self, recommendation: Recommendation) -> Recommendation:
        saved = self._store.recommendations.save(recommendation.recommendation_id, recommendation)
        await publish(
            RecommendationGeneratedEvent(
                recommendation_id=saved.recommendation_id,
                kind=saved.kind,
                subject_id=saved.subject_id,
                count=len(saved.items),
            )
        )
        return saved

    async def recommend_products(self, *, buyer_id: str = "", budget: float | None = None) -> Recommendation:
        products = [
            p for p in self._store.agro_products.list_all() if p.status == AvailabilityStatus.AVAILABLE
        ]
        if budget is not None:
            products = [p for p in products if p.price <= budget]
        products = sorted(products, key=lambda p: p.price)[:10]
        buyer = None
        if buyer_id:
            for profile in self._store.buyer_profiles.list_all():
                if profile.buyer_id == buyer_id or profile.profile_id == buyer_id:
                    buyer = profile
                    break
        if buyer and buyer.preferred_crops:
            preferred = [p for p in products if p.crop_id in buyer.preferred_crops]
            rest = [p for p in products if p not in preferred]
            products = preferred + rest
        return await self._save(
            Recommendation(
                kind="product",
                subject_id=buyer_id,
                items=[p.to_dict() for p in products[:8]],
                score=float(len(products)),
                rationale="Available catalog ranked by preference and price",
            )
        )

    async def recommend_buyers(self, offer_id: str) -> Recommendation:
        offer = self._store.sales_offers.get(offer_id)
        items: list[dict[str, Any]] = []
        if offer is not None:
            items = await self._trading_ai.recommend_buyers(offer, self._store.buyer_profiles.list_all())
        return await self._save(
            Recommendation(
                kind="buyer",
                subject_id=offer_id,
                items=items,
                score=float(items[0]["match_score"]) if items else 0.0,
                rationale="Buyer preference and budget match",
            )
        )

    async def recommend_suppliers(self, request_id: str) -> Recommendation:
        request = self._store.purchase_requests.get(request_id)
        items: list[dict[str, Any]] = []
        if request is not None:
            items = await self._trading_ai.recommend_suppliers(
                request, self._store.supplier_profiles.list_all()
            )
        return await self._save(
            Recommendation(
                kind="supplier",
                subject_id=request_id,
                items=items,
                score=float(items[0]["match_score"]) if items else 0.0,
                rationale="Supplier product capability match",
            )
        )

    async def recommend_contracts(self, order_id: str) -> Recommendation:
        order = self._store.marketplace_orders.get(order_id)
        items: list[dict[str, Any]] = []
        if order is not None:
            items = [
                {
                    "template": "standard_grain_contract",
                    "suggested_terms": {
                        "quantity": order.quantity,
                        "unit_price": order.unit_price,
                        "currency": order.currency,
                        "incoterms": "FOB",
                        "quality": "Grade A, moisture <=14%",
                    },
                },
                {
                    "template": "export_ready_contract",
                    "suggested_terms": {
                        "quantity": order.quantity,
                        "unit_price": order.unit_price * 1.05,
                        "documents": ["phytosanitary", "certificate_of_origin"],
                    },
                },
            ]
        return await self._save(
            Recommendation(
                kind="contract",
                subject_id=order_id,
                items=items,
                score=80.0 if items else 0.0,
                rationale="Contract templates based on order profile",
            )
        )

    def inventory_optimization(self, *, warehouse_id: str = "") -> dict[str, Any]:
        items = self._store.inventory_items.list_all()
        if warehouse_id:
            items = [i for i in items if i.warehouse_id == warehouse_id]
        low = [i.to_dict() for i in items if i.available_quantity < max(1.0, i.quantity * 0.2)]
        excess = [i.to_dict() for i in items if i.available_quantity > 50]
        return {
            "warehouse_id": warehouse_id,
            "low_stock": low,
            "excess_stock": excess,
            "actions": [
                {"type": "replenish", "count": len(low)},
                {"type": "transfer_or_list", "count": len(excess)},
            ],
        }

    def warehouse_optimization(self) -> dict[str, Any]:
        warehouses = self._store.agro_warehouses.list_all()
        suggestions = []
        for wh in warehouses:
            util = (wh.used_tons / wh.capacity_tons) if wh.capacity_tons else 0.0
            if util > 0.85:
                suggestions.append(
                    {
                        "warehouse_id": wh.warehouse_id,
                        "action": "expand_or_transfer_out",
                        "utilization": round(util, 2),
                    }
                )
            elif util < 0.3 and wh.capacity_tons > 0:
                suggestions.append(
                    {
                        "warehouse_id": wh.warehouse_id,
                        "action": "consolidate_inbound",
                        "utilization": round(util, 2),
                    }
                )
        return {"suggestions": suggestions, "warehouses": len(warehouses)}

    async def detect_trade_opportunities(self) -> Recommendation:
        offers = self._store.sales_offers.list_all()
        requests = self._store.purchase_requests.list_all()
        opportunities = self._trading_ai.detect_opportunities(offers, requests)
        await publish(
            TradeOpportunityDetectedEvent(
                opportunity_count=len(opportunities),
                top_score=float(opportunities[0]["score"]) if opportunities else 0.0,
                opportunities=opportunities[:10],
            )
        )
        return await self._save(
            Recommendation(
                kind="trade_opportunity",
                subject_id="marketplace",
                items=opportunities[:10],
                score=float(opportunities[0]["score"]) if opportunities else 0.0,
                rationale="Offer/request matching opportunities",
            )
        )

    def list_recommendations(self, *, kind: str | None = None) -> list[Recommendation]:
        items = self._store.recommendations.list_all()
        if kind:
            items = [r for r in items if r.kind == kind]
        return items


recommendation_engine = RecommendationEngine()
