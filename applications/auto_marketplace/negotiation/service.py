# Negotiation Assistant — offer guidance and counter-proposals.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from applications.auto_marketplace.ai_sales.events import OfferGeneratedEvent
from applications.auto_marketplace.ai_sales.integration import ai_sales_platform_bridge
from applications.auto_marketplace.ai_sales.models import SalesOffer
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class NegotiationService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    async def suggest_counter_offer(self, deal_id: str, proposed_amount: float) -> dict[str, Any]:
        analysis = await ai_sales_platform_bridge.reason(
            "Suggest counter offer for vehicle deal",
            {"deal_id": deal_id, "proposed_amount": proposed_amount},
        )
        counter = round(proposed_amount * 0.97, 2)
        if "counter_offer" in analysis:
            counter = float(analysis["counter_offer"])
        return {
            "deal_id": deal_id,
            "proposed_amount": proposed_amount,
            "counter_offer": counter,
            "talking_points": analysis.get("talking_points", ["Flexible financing", "Extended warranty"]),
        }

    async def generate_offer(
        self,
        customer_id: str,
        vehicle_id: str,
        *,
        dealer_id: str = "",
        amount: float = 0.0,
        trade_in_value: float = 0.0,
        accessories: list[str] | None = None,
    ) -> SalesOffer:
        if amount <= 0:
            vehicle = self._store.catalog_vehicles.get(vehicle_id) or self._store.vehicles.get(vehicle_id)
            amount = float(getattr(vehicle, "price", 0) or 0) if vehicle else 25000.0
        offer = SalesOffer(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            dealer_id=dealer_id,
            amount=amount,
            trade_in_value=trade_in_value,
            accessories=accessories or [],
            status="draft",
        )
        self._store.ai_offers.save(offer.offer_id, offer)
        await publish(
            OfferGeneratedEvent(
                offer_id=offer.offer_id,
                customer_id=customer_id,
                vehicle_id=vehicle_id,
                amount=amount,
            )
        )
        return offer

    def get_offer(self, offer_id: str) -> SalesOffer | None:
        return self._store.ai_offers.get(offer_id)

    def list_offers(self, customer_id: str | None = None) -> list[SalesOffer]:
        offers = self._store.ai_offers.list_all()
        if customer_id:
            return [o for o in offers if o.customer_id == customer_id]
        return offers

    async def negotiate_terms(self, offer_id: str, customer_counter: float) -> dict[str, Any]:
        offer = self._store.ai_offers.get(offer_id)
        if offer is None:
            raise ValueError(f"Offer not found: {offer_id}")
        gap = offer.amount - customer_counter
        acceptable = gap / max(offer.amount, 1) <= 0.05
        revised = round((offer.amount + customer_counter) / 2, 2) if not acceptable else customer_counter
        return {
            "offer_id": offer_id,
            "original_amount": offer.amount,
            "customer_counter": customer_counter,
            "revised_amount": revised,
            "acceptable": acceptable,
        }


negotiation_service = NegotiationService()
