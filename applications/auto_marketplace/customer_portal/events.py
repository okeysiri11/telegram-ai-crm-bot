# Portal events — Sprint 6.7.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class CustomerRegisteredEvent(BaseEvent):
    user_id: str = ""
    email: str = ""
    customer_id: str = ""


@dataclass(kw_only=True)
class DealerLoggedInEvent(BaseEvent):
    user_id: str = ""
    dealer_id: str = ""


@dataclass(kw_only=True)
class FavoriteAddedEvent(BaseEvent):
    user_id: str = ""
    vehicle_id: str = ""


@dataclass(kw_only=True)
class VehicleViewedEvent(BaseEvent):
    user_id: str = ""
    vehicle_id: str = ""
    source: str = "portal"


@dataclass(kw_only=True)
class OfferRequestedEvent(BaseEvent):
    request_id: str = ""
    customer_id: str = ""
    vehicle_id: str = ""


@dataclass(kw_only=True)
class TestDriveBookedEvent(BaseEvent):
    booking_id: str = ""
    customer_id: str = ""
    vehicle_id: str = ""


@dataclass(kw_only=True)
class NotificationSentEvent(BaseEvent):
    notification_id: str = ""
    user_id: str = ""
    channel: str = ""


@dataclass(kw_only=True)
class PartnerConnectedEvent(BaseEvent):
    connection_id: str = ""
    partner_id: str = ""
    partner_type: str = ""
