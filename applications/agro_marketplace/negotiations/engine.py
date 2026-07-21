# NegotiationEngine — counter offers and term negotiation.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from applications.agro_marketplace.marketplace.ai_integration import TradingAIIntegration, trading_ai
from applications.agro_marketplace.marketplace.events import NegotiationStartedEvent
from applications.agro_marketplace.marketplace.models import (
    DeliveryAgreement,
    Negotiation,
    NegotiationStatus,
    OfferStatus,
)
from applications.agro_marketplace.marketplace.workflow import TradingWorkflowBridge, trading_workflow
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class NegotiationEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: TradingAIIntegration | None = None,
        workflow: TradingWorkflowBridge | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or trading_ai
        self._workflow = workflow or trading_workflow

    def get(self, negotiation_id: str) -> Negotiation:
        negotiation = self._store.negotiations.get(negotiation_id)
        if negotiation is None:
            raise NotFoundError("Negotiation", negotiation_id)
        return negotiation

    def list_negotiations(self, *, status: NegotiationStatus | None = None) -> list[Negotiation]:
        items = self._store.negotiations.list_all()
        if status:
            items = [n for n in items if n.status == status]
        return items

    async def start(
        self,
        *,
        offer_id: str,
        buyer_id: str,
        seller_id: str,
        price: float,
        quantity: float,
        request_id: str = "",
        delivery_terms: str = "",
    ) -> Negotiation:
        offer = self._store.sales_offers.get(offer_id)
        if offer is None:
            raise NotFoundError("SalesOffer", offer_id)
        negotiation = Negotiation(
            offer_id=offer_id,
            request_id=request_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            current_price=price,
            current_quantity=quantity,
            delivery_terms=delivery_terms,
            status=NegotiationStatus.OPEN,
            rounds=[{"type": "open", "price": price, "quantity": quantity, "at": time.time()}],
        )
        offer.status = OfferStatus.NEGOTIATING
        offer.updated_at = time.time()
        self._store.sales_offers.save(offer_id, offer)
        saved = self._store.negotiations.save(negotiation.negotiation_id, negotiation)
        await self._workflow.start_negotiation_workflow(saved.negotiation_id)
        await publish(
            NegotiationStartedEvent(
                negotiation_id=saved.negotiation_id,
                offer_id=offer_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
            )
        )
        self._workflow.notify(buyer_id, "Negotiation started", saved.negotiation_id)
        self._workflow.notify(seller_id, "Negotiation started", saved.negotiation_id)
        return saved

    async def counter_offer(
        self,
        negotiation_id: str,
        *,
        price: float | None = None,
        quantity: float | None = None,
        delivery_terms: str | None = None,
        actor_id: str = "",
    ) -> Negotiation:
        negotiation = self.get(negotiation_id)
        if negotiation.status in {NegotiationStatus.AGREED, NegotiationStatus.CANCELLED}:
            raise ValidationError("negotiation is closed")
        if price is not None:
            negotiation.current_price = price
        if quantity is not None:
            negotiation.current_quantity = quantity
        if delivery_terms is not None:
            negotiation.delivery_terms = delivery_terms
        negotiation.status = NegotiationStatus.COUNTERED
        negotiation.updated_at = time.time()
        negotiation.rounds.append(
            {
                "type": "counter",
                "actor_id": actor_id,
                "price": negotiation.current_price,
                "quantity": negotiation.current_quantity,
                "delivery_terms": negotiation.delivery_terms,
                "at": time.time(),
            }
        )
        return self._store.negotiations.save(negotiation_id, negotiation)

    async def negotiate_price(self, negotiation_id: str, price: float, *, actor_id: str = "") -> Negotiation:
        return await self.counter_offer(negotiation_id, price=price, actor_id=actor_id)

    async def negotiate_quantity(self, negotiation_id: str, quantity: float, *, actor_id: str = "") -> Negotiation:
        return await self.counter_offer(negotiation_id, quantity=quantity, actor_id=actor_id)

    async def negotiate_delivery(
        self,
        negotiation_id: str,
        delivery_terms: str,
        *,
        origin: str = "",
        destination: str = "",
        delivery_by: float = 0.0,
        carrier: str = "",
        actor_id: str = "",
    ) -> tuple[Negotiation, DeliveryAgreement]:
        negotiation = await self.counter_offer(
            negotiation_id,
            delivery_terms=delivery_terms,
            actor_id=actor_id,
        )
        agreement = DeliveryAgreement(
            negotiation_id=negotiation_id,
            origin=origin,
            destination=destination,
            delivery_by=delivery_by,
            carrier=carrier,
            terms={"delivery_terms": delivery_terms},
        )
        saved_agreement = self._store.delivery_agreements.save(agreement.agreement_id, agreement)
        return negotiation, saved_agreement

    async def agree(self, negotiation_id: str) -> Negotiation:
        negotiation = self.get(negotiation_id)
        negotiation.status = NegotiationStatus.AGREED
        negotiation.updated_at = time.time()
        negotiation.rounds.append({"type": "agreed", "at": time.time()})
        return self._store.negotiations.save(negotiation_id, negotiation)

    async def assistant_suggestion(self, negotiation_id: str, *, target_price: float = 0.0) -> dict[str, Any]:
        negotiation = self.get(negotiation_id)
        return await self._ai.suggest_negotiation(
            current_price=negotiation.current_price,
            current_quantity=negotiation.current_quantity,
            target_price=target_price,
        )


negotiation_engine = NegotiationEngine()
