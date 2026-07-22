# CRMService — leads, deals, appointments, negotiations, reservations (Sprint 10.1).

from __future__ import annotations

from applications.auto_marketplace.foundation.models import (
    Appointment,
    AppointmentStatus,
    BuyerRequest,
    Negotiation,
    NegotiationStatus,
)
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.models import Deal, DealStatus, Lead, LeadStatus, Offer, Reservation
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CRMService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create_lead(self, lead: Lead) -> Lead:
        return self._store.leads.save(lead.lead_id, lead)

    def get_lead(self, lead_id: str) -> Lead:
        lead = self._store.leads.get(lead_id)
        if lead is None:
            raise NotFoundError("Lead", lead_id)
        return lead

    def list_leads(self, *, status: LeadStatus | None = None) -> list[Lead]:
        items = self._store.leads.list_all()
        if status:
            items = [item for item in items if item.status == status]
        return items

    def update_lead_status(self, lead_id: str, status: LeadStatus) -> Lead:
        lead = self.get_lead(lead_id)
        lead.status = status
        return self._store.leads.save(lead_id, lead)

    def create_request(self, request: BuyerRequest) -> BuyerRequest:
        if not request.buyer_id:
            raise ValidationError("buyer_id is required")
        return self._store.buyer_requests.save(request.request_id, request)

    def list_requests(self, *, buyer_id: str = "") -> list[BuyerRequest]:
        items = self._store.buyer_requests.list_all()
        if buyer_id:
            items = [r for r in items if r.buyer_id == buyer_id]
        return items

    def schedule_appointment(self, appointment: Appointment) -> Appointment:
        if not appointment.buyer_id or not appointment.dealer_id:
            raise ValidationError("buyer_id and dealer_id are required")
        return self._store.appointments.save(appointment.appointment_id, appointment)

    def list_appointments(self, *, buyer_id: str = "", dealer_id: str = "") -> list[Appointment]:
        items = self._store.appointments.list_all()
        if buyer_id:
            items = [a for a in items if a.buyer_id == buyer_id]
        if dealer_id:
            items = [a for a in items if a.dealer_id == dealer_id]
        return items

    def update_appointment_status(self, appointment_id: str, status: AppointmentStatus) -> Appointment:
        appointment = self._store.appointments.get(appointment_id)
        if appointment is None:
            raise NotFoundError("Appointment", appointment_id)
        appointment.status = status
        return self._store.appointments.save(appointment_id, appointment)

    def start_negotiation(self, negotiation: Negotiation) -> Negotiation:
        if not negotiation.vehicle_id or not negotiation.buyer_id:
            raise ValidationError("vehicle_id and buyer_id are required")
        negotiation.history.append(
            {"event": "offer", "price": negotiation.offer_price, "status": negotiation.status.value}
        )
        return self._store.negotiations.save(negotiation.negotiation_id, negotiation)

    def counter_negotiation(self, negotiation_id: str, counter_price: float) -> Negotiation:
        negotiation = self._store.negotiations.get(negotiation_id)
        if negotiation is None:
            raise NotFoundError("Negotiation", negotiation_id)
        negotiation.counter_price = counter_price
        negotiation.status = NegotiationStatus.COUNTERED
        negotiation.history.append({"event": "counter", "price": counter_price})
        return self._store.negotiations.save(negotiation_id, negotiation)

    def list_negotiations(self, *, buyer_id: str = "") -> list[Negotiation]:
        items = self._store.negotiations.list_all()
        if buyer_id:
            items = [n for n in items if n.buyer_id == buyer_id]
        return items

    def reserve_vehicle(self, reservation: Reservation) -> Reservation:
        if not reservation.vehicle_id or not reservation.customer_id:
            raise ValidationError("vehicle_id and customer_id are required")
        return self._store.reservations.save(reservation.reservation_id, reservation)

    def list_reservations(self, *, customer_id: str = "", active_only: bool = True) -> list[Reservation]:
        items = self._store.reservations.list_all()
        if customer_id:
            items = [r for r in items if r.customer_id == customer_id]
        if active_only:
            items = [r for r in items if r.active]
        return items

    def customer_history(self, customer_id: str) -> dict:
        return {
            "customer_id": customer_id,
            "leads": [l.to_dict() for l in self.list_leads() if l.customer_id == customer_id],
            "requests": [r.to_dict() for r in self.list_requests(buyer_id=customer_id)],
            "appointments": [a.to_dict() for a in self.list_appointments(buyer_id=customer_id)],
            "negotiations": [n.to_dict() for n in self.list_negotiations(buyer_id=customer_id)],
            "reservations": [r.to_dict() for r in self.list_reservations(customer_id=customer_id, active_only=False)],
            "deals": [d.to_dict() for d in self._store.deals.list_all() if d.customer_id == customer_id],
        }

    def create_deal(self, deal: Deal) -> Deal:
        return self._store.deals.save(deal.deal_id, deal)

    def get_deal(self, deal_id: str) -> Deal:
        deal = self._store.deals.get(deal_id)
        if deal is None:
            raise NotFoundError("Deal", deal_id)
        return deal

    def add_offer(self, deal_id: str, offer: Offer) -> Deal:
        deal = self.get_deal(deal_id)
        offer.deal_id = deal_id
        deal.offers.append(offer)
        deal.status = DealStatus.NEGOTIATING
        return self._store.deals.save(deal_id, deal)

    def close_deal(self, deal_id: str, final_price: float) -> Deal:
        deal = self.get_deal(deal_id)
        deal.final_price = final_price
        deal.status = DealStatus.CLOSED
        return self._store.deals.save(deal_id, deal)

    def metrics(self) -> dict:
        return {
            "leads": self._store.leads.count(),
            "requests": self._store.buyer_requests.count(),
            "appointments": self._store.appointments.count(),
            "negotiations": self._store.negotiations.count(),
            "reservations": self._store.reservations.count(),
            "deals": self._store.deals.count(),
        }


crm_service = CRMService()
