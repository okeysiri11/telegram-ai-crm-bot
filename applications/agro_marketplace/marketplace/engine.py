# MarketplaceEngine — listings, requests, offers, matching, deals, orders.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from applications.agro_marketplace.marketplace.ai_integration import TradingAIIntegration, trading_ai
from applications.agro_marketplace.marketplace.events import (
    OfferMatchedEvent,
    OfferPublishedEvent,
    OrderConfirmedEvent,
    TradeCompletedEvent,
)
from applications.agro_marketplace.marketplace.models import (
    DealStatus,
    MarketplaceDeal,
    MarketplaceOrder,
    MarketplaceOrderStatus,
    OfferStatus,
    PurchaseRequest,
    SalesOffer,
)
from applications.agro_marketplace.marketplace.workflow import TradingWorkflowBridge, trading_workflow
from applications.agro_marketplace.negotiations.engine import NegotiationEngine, negotiation_engine
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import MarketplaceListing
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class MarketplaceEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: TradingAIIntegration | None = None,
        workflow: TradingWorkflowBridge | None = None,
        negotiations: NegotiationEngine | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or trading_ai
        self._workflow = workflow or trading_workflow
        self._negotiations = negotiations or negotiation_engine

    def create_listing(self, listing: MarketplaceListing) -> MarketplaceListing:
        return self._store.listings.save(listing.listing_id, listing)

    def list_listings(self, *, active_only: bool = True) -> list[MarketplaceListing]:
        items = self._store.listings.list_all()
        if active_only:
            items = [i for i in items if i.is_active]
        return items

    def create_purchase_request(self, request: PurchaseRequest) -> PurchaseRequest:
        if request.quantity <= 0:
            raise ValidationError("quantity must be positive")
        return self._store.purchase_requests.save(request.request_id, request)

    def list_purchase_requests(self, *, status: str | None = "open") -> list[PurchaseRequest]:
        items = self._store.purchase_requests.list_all()
        if status:
            items = [r for r in items if r.status == status]
        return items

    async def publish_offer(self, offer: SalesOffer) -> SalesOffer:
        if offer.quantity <= 0 or offer.price < 0:
            raise ValidationError("quantity must be positive and price non-negative")
        offer.status = OfferStatus.PUBLISHED
        offer.updated_at = time.time()
        saved = self._store.sales_offers.save(offer.offer_id, offer)
        # Sync lightweight legacy offer
        from applications.agro_marketplace.shared.models import Offer

        self._store.offers.save(
            saved.offer_id,
            Offer(
                offer_id=saved.offer_id,
                product_id=saved.product_id,
                buyer_id="",
                price=saved.price,
                quantity=saved.quantity,
                status=saved.status.value,
            ),
        )
        await self._workflow.start_offer_approval(saved.offer_id, {"price": saved.price})
        await publish(
            OfferPublishedEvent(
                offer_id=saved.offer_id,
                seller_id=saved.seller_id,
                product_id=saved.product_id,
                price=saved.price,
                quantity=saved.quantity,
            )
        )
        return saved

    def list_offers(self, *, status: OfferStatus | None = None) -> list[SalesOffer]:
        items = self._store.sales_offers.list_all()
        if status:
            items = [o for o in items if o.status == status]
        return items

    def get_offer(self, offer_id: str) -> SalesOffer:
        offer = self._store.sales_offers.get(offer_id)
        if offer is None:
            raise NotFoundError("SalesOffer", offer_id)
        return offer

    async def match_offer(self, offer_id: str, request_id: str | None = None) -> dict[str, Any]:
        offer = self.get_offer(offer_id)
        requests = self.list_purchase_requests(status="open")
        if request_id:
            request = self._store.purchase_requests.get(request_id)
            if request is None:
                raise NotFoundError("PurchaseRequest", request_id)
            candidates = [request]
        else:
            candidates = requests
        best = None
        best_score = -1.0
        for request in candidates:
            score = self._ai.match_score(offer, request)
            if score > best_score:
                best_score = score
                best = request
        if best is None or best_score < 30:
            return {"matched": False, "offer_id": offer_id, "score": best_score}
        offer.status = OfferStatus.MATCHED
        offer.matched_request_id = best.request_id
        offer.updated_at = time.time()
        self._store.sales_offers.save(offer_id, offer)
        best.status = "matched"
        self._store.purchase_requests.save(best.request_id, best)
        await publish(
            OfferMatchedEvent(offer_id=offer_id, request_id=best.request_id, score=best_score)
        )
        return {
            "matched": True,
            "offer_id": offer_id,
            "request_id": best.request_id,
            "score": best_score,
            "buyer_id": best.buyer_id,
            "seller_id": offer.seller_id,
        }

    async def start_negotiation_from_match(self, offer_id: str, request_id: str) -> Any:
        offer = self.get_offer(offer_id)
        request = self._store.purchase_requests.get(request_id)
        if request is None:
            raise NotFoundError("PurchaseRequest", request_id)
        return await self._negotiations.start(
            offer_id=offer_id,
            buyer_id=request.buyer_id,
            seller_id=offer.seller_id,
            price=offer.price,
            quantity=min(offer.quantity, request.quantity) if request.quantity else offer.quantity,
            request_id=request_id,
        )

    def create_order(self, order: MarketplaceOrder) -> MarketplaceOrder:
        if order.quantity <= 0:
            raise ValidationError("quantity must be positive")
        order.status = MarketplaceOrderStatus.PENDING_APPROVAL
        order.updated_at = time.time()
        return self._store.marketplace_orders.save(order.order_id, order)

    def list_orders(self) -> list[MarketplaceOrder]:
        return self._store.marketplace_orders.list_all()

    def get_order(self, order_id: str) -> MarketplaceOrder:
        order = self._store.marketplace_orders.get(order_id)
        if order is None:
            raise NotFoundError("MarketplaceOrder", order_id)
        return order

    async def confirm_order(self, order_id: str) -> MarketplaceOrder:
        order = self.get_order(order_id)
        order.status = MarketplaceOrderStatus.CONFIRMED
        order.confirmed_at = time.time()
        order.updated_at = time.time()
        saved = self._store.marketplace_orders.save(order_id, order)
        await self._workflow.start_order_workflow(order_id)
        await publish(
            OrderConfirmedEvent(
                order_id=saved.order_id,
                buyer_id=saved.buyer_id,
                seller_id=saved.seller_id,
                total=saved.total,
            )
        )
        self._workflow.notify(saved.buyer_id, "Order confirmed", saved.order_id)
        self._workflow.notify(saved.seller_id, "Order confirmed", saved.order_id)
        return saved

    def create_deal(self, deal: MarketplaceDeal) -> MarketplaceDeal:
        return self._store.marketplace_deals.save(deal.deal_id, deal)

    async def complete_trade(self, deal_id: str) -> MarketplaceDeal:
        deal = self._store.marketplace_deals.get(deal_id)
        if deal is None:
            raise NotFoundError("MarketplaceDeal", deal_id)
        deal.status = DealStatus.COMPLETED
        deal.completed_at = time.time()
        saved = self._store.marketplace_deals.save(deal_id, deal)
        if saved.order_id:
            try:
                order = self.get_order(saved.order_id)
                order.status = MarketplaceOrderStatus.COMPLETED
                order.updated_at = time.time()
                self._store.marketplace_orders.save(order.order_id, order)
            except NotFoundError:
                pass
        await publish(
            TradeCompletedEvent(deal_id=saved.deal_id, order_id=saved.order_id, amount=saved.amount)
        )
        return saved

    def opportunities(self) -> list[dict[str, Any]]:
        return self._ai.detect_opportunities(self.list_offers(), self.list_purchase_requests())

    def metrics(self) -> dict[str, Any]:
        return {
            "listings": self._store.listings.count(),
            "purchase_requests": self._store.purchase_requests.count(),
            "sales_offers": self._store.sales_offers.count(),
            "orders": self._store.marketplace_orders.count(),
            "deals": self._store.marketplace_deals.count(),
            "negotiations": self._store.negotiations.count(),
        }


marketplace_engine = MarketplaceEngine()
