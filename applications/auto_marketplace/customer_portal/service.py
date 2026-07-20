# Customer Portal — search, bookings, offers, history, AI assistant.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from applications.auto_marketplace.ai_sales.models import AgentType
from applications.auto_marketplace.authentication.models import OfferRequest, TestDriveBooking, TradeInRequest
from applications.auto_marketplace.customer_portal.events import OfferRequestedEvent, TestDriveBookedEvent, VehicleViewedEvent
from applications.auto_marketplace.crm.models import CRMLead, LeadSource
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CustomerPortalService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    async def search_vehicles(self, criteria: dict[str, Any]) -> list[dict]:
        try:
            from applications.auto_marketplace.filters.criteria import VehicleSearchCriteria
            from applications.auto_marketplace.filters.search_engine import search_engine

            vc = VehicleSearchCriteria(
                brand=criteria.get("brand", criteria.get("make", "")),
                model=criteria.get("model", ""),
                price_min=float(criteria.get("price_min", 0)),
                price_max=float(criteria.get("price_max", 0)) or None,
                limit=int(criteria.get("limit", 20)),
            )
            return await search_engine.search(vc)
        except Exception:
            vehicles = self._store.catalog_vehicles.list_all() or self._store.vehicles.list_all()
            return [v.to_dict() for v in vehicles[: int(criteria.get("limit", 20))]]

    async def smart_search(self, query: str, user_id: str = "") -> list[dict]:
        from applications.auto_marketplace.ai_sales.engine import ai_sales_engine

        result = await ai_sales_engine.dispatch_agent(AgentType.CUSTOMER_ASSISTANT, {"message": query})
        criteria = {"limit": 10}
        if "suv" in query.lower():
            criteria["body_type"] = "suv"
        if "under" in query.lower():
            parts = query.split()
            for i, p in enumerate(parts):
                if p == "under" and i + 1 < len(parts):
                    try:
                        criteria["price_max"] = float(parts[i + 1].replace("$", "").replace(",", ""))
                    except ValueError:
                        pass
        vehicles = await self.search_vehicles(criteria)
        return {"suggestion": result.get("response", ""), "vehicles": vehicles}  # type: ignore[return-value]

    async def view_vehicle(self, user_id: str, vehicle_id: str, *, source: str = "portal") -> dict:
        vehicle = self._store.catalog_vehicles.get(vehicle_id) or self._store.vehicles.get(vehicle_id)
        await publish(VehicleViewedEvent(user_id=user_id, vehicle_id=vehicle_id, source=source))
        return vehicle.to_dict() if vehicle and hasattr(vehicle, "to_dict") else {"vehicle_id": vehicle_id}

    async def book_test_drive(
        self, user_id: str, *, customer_id: str, vehicle_id: str, dealer_id: str, scheduled_at: float
    ) -> TestDriveBooking:
        booking = TestDriveBooking(
            user_id=user_id, customer_id=customer_id, vehicle_id=vehicle_id, dealer_id=dealer_id, scheduled_at=scheduled_at
        )
        self._store.test_drive_bookings.save(booking.booking_id, booking)
        lead = CRMLead(customer_id=customer_id, vehicle_id=vehicle_id, dealer_id=dealer_id, source=LeadSource.WEB)
        self._store.crm_leads.save(lead.lead_id, lead)
        await publish(TestDriveBookedEvent(booking_id=booking.booking_id, customer_id=customer_id, vehicle_id=vehicle_id))
        return booking

    async def request_trade_in(
        self, user_id: str, *, customer_id: str, vin: str, make: str, model: str, year: int, mileage_km: int
    ) -> TradeInRequest:
        req = TradeInRequest(
            user_id=user_id, customer_id=customer_id, vin=vin, make=make, model=model, year=year, mileage_km=mileage_km
        )
        try:
            from applications.auto_marketplace.pricing.service import pricing_service
            from applications.auto_marketplace.shared.models import TradeIn, VehicleSpecification

            ti = TradeIn(customer_id=customer_id, specification=VehicleSpecification(make=make, model=model, year=year, mileage_km=mileage_km, vin=vin))
            req.estimated_value = pricing_service.estimate_trade_in(ti)
        except Exception:
            req.estimated_value = max(year - 2000, 1) * 500.0
        self._store.trade_in_requests.save(req.request_id, req)
        return req

    async def request_offer(
        self, user_id: str, *, customer_id: str, vehicle_id: str, dealer_id: str, proposed_amount: float
    ) -> OfferRequest:
        req = OfferRequest(
            user_id=user_id, customer_id=customer_id, vehicle_id=vehicle_id, dealer_id=dealer_id, proposed_amount=proposed_amount
        )
        try:
            from applications.auto_marketplace.ai_sales.engine import ai_sales_engine

            offer = await ai_sales_engine.negotiation.generate_offer(customer_id, vehicle_id, dealer_id=dealer_id, amount=proposed_amount)
            req.offer_id = offer.offer_id
        except Exception:
            pass
        self._store.offer_requests.save(req.request_id, req)
        await publish(OfferRequestedEvent(request_id=req.request_id, customer_id=customer_id, vehicle_id=vehicle_id))
        return req

    def purchase_history(self, customer_id: str) -> list[dict]:
        deals = [d for d in self._store.crm_deals.list_all() if d.customer_id == customer_id and d.stage.value == "closed_won"]
        payments = [p for p in self._store.finance_payments.list_all() if p.customer_id == customer_id]
        return {
            "deals": [d.to_dict() for d in deals],
            "payments": [p.to_dict() for p in payments],
        }  # type: ignore[return-value]

    async def ai_assistant(self, user_id: str, message: str) -> dict:
        from applications.auto_marketplace.ai_sales.engine import ai_sales_engine

        return await ai_sales_engine.dispatch_agent(AgentType.CUSTOMER_ASSISTANT, {"message": message, "user_id": user_id})

    async def recommendations(self, customer_id: str) -> list[dict]:
        from applications.auto_marketplace.ai_sales.engine import ai_sales_engine

        items = await ai_sales_engine.recommendations.personalized(customer_id)
        return [i.to_dict() for i in items]


customer_portal_service = CustomerPortalService()
