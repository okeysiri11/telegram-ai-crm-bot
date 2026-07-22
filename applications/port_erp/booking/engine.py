# Booking Engine — request → quote → reservation → confirmation → execution → completion.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.multimodal.events import BookingConfirmedEvent, BookingCreatedEvent
from applications.port_erp.multimodal.models import BookingStatus, TransportBooking, TransportMode
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


_WORKFLOW = [
    BookingStatus.REQUEST,
    BookingStatus.QUOTE,
    BookingStatus.RESERVATION,
    BookingStatus.CONFIRMATION,
    BookingStatus.EXECUTION,
    BookingStatus.COMPLETION,
]


class BookingEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def workflow_statuses(self) -> list[str]:
        return [s.value for s in _WORKFLOW] + [BookingStatus.CANCELLATION.value]

    async def create(self, booking: TransportBooking) -> TransportBooking:
        if not booking.origin or not booking.destination:
            raise ValidationError("origin and destination are required")
        booking.status = BookingStatus.REQUEST
        saved = self._store.transport_bookings.save(booking.booking_id, booking)
        await publish(
            BookingCreatedEvent(
                booking_id=saved.booking_id,
                mode=saved.mode.value,
                origin=saved.origin,
                destination=saved.destination,
            )
        )
        return saved

    def get(self, booking_id: str) -> TransportBooking:
        item = self._store.transport_bookings.get(booking_id)
        if item is None:
            raise NotFoundError("TransportBooking", booking_id)
        return item

    def list_bookings(self, *, status: BookingStatus | None = None) -> list[TransportBooking]:
        items = self._store.transport_bookings.list_all()
        if status:
            items = [b for b in items if b.status == status]
        return items

    def quote(self, booking_id: str, *, amount: float, currency: str = "USD") -> TransportBooking:
        booking = self.get(booking_id)
        if amount < 0:
            raise ValidationError("amount must be non-negative")
        booking.quoted_amount = amount
        booking.currency = currency
        booking.status = BookingStatus.QUOTE
        return self._store.transport_bookings.save(booking_id, booking)

    def reserve(self, booking_id: str) -> TransportBooking:
        return self._advance(booking_id, BookingStatus.RESERVATION)

    async def confirm(self, booking_id: str, *, carrier_id: str = "") -> TransportBooking:
        booking = self.get(booking_id)
        if carrier_id:
            booking.carrier_id = carrier_id
        booking.status = BookingStatus.CONFIRMATION
        booking.confirmed_at = time.time()
        saved = self._store.transport_bookings.save(booking_id, booking)
        await publish(
            BookingConfirmedEvent(
                booking_id=booking_id,
                carrier_id=saved.carrier_id,
                quoted_amount=saved.quoted_amount,
            )
        )
        return saved

    def execute(self, booking_id: str) -> TransportBooking:
        return self._advance(booking_id, BookingStatus.EXECUTION)

    def complete(self, booking_id: str) -> TransportBooking:
        booking = self._advance(booking_id, BookingStatus.COMPLETION)
        booking.completed_at = time.time()
        return self._store.transport_bookings.save(booking_id, booking)

    def cancel(self, booking_id: str, *, notes: str = "") -> TransportBooking:
        booking = self.get(booking_id)
        if booking.status == BookingStatus.COMPLETION:
            raise ValidationError("completed booking cannot be cancelled")
        booking.status = BookingStatus.CANCELLATION
        if notes:
            booking.notes = notes
        return self._store.transport_bookings.save(booking_id, booking)

    def _advance(self, booking_id: str, target: BookingStatus) -> TransportBooking:
        booking = self.get(booking_id)
        if booking.status == BookingStatus.CANCELLATION:
            raise ValidationError("cancelled booking cannot advance")
        if target not in _WORKFLOW:
            raise ValidationError(f"invalid status: {target}")
        current_idx = _WORKFLOW.index(booking.status) if booking.status in _WORKFLOW else -1
        target_idx = _WORKFLOW.index(target)
        if target_idx < current_idx:
            raise ValidationError("cannot move booking backwards")
        booking.status = target
        return self._store.transport_bookings.save(booking_id, booking)


booking_engine = BookingEngine()
