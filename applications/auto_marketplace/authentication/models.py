# Portal authentication models — Sprint 6.7.

from __future__ import annotations

import enum
import hashlib
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class PortalRole(str, enum.Enum):
    CUSTOMER = "customer"
    DEALER = "dealer"
    PARTNER = "partner"
    ADMINISTRATOR = "administrator"
    OWNER = "owner"
    AI_AGENT = "ai_agent"


@dataclass
class PortalUser:
    user_id: str = field(default_factory=_id)
    email: str = ""
    password_hash: str = ""
    role: PortalRole = PortalRole.CUSTOMER
    customer_id: str = ""
    dealer_id: str = ""
    partner_id: str = ""
    display_name: str = ""
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self, *, include_sensitive: bool = False) -> dict[str, Any]:
        data = {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role.value,
            "customer_id": self.customer_id,
            "dealer_id": self.dealer_id,
            "partner_id": self.partner_id,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }
        if include_sensitive:
            data["metadata"] = dict(self.metadata)
        return data


@dataclass
class AuthToken:
    token_id: str = field(default_factory=_id)
    user_id: str = ""
    access_token: str = ""
    refresh_token: str = ""
    expires_at: float = field(default_factory=lambda: _ts() + 3600)
    role: PortalRole = PortalRole.CUSTOMER
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "token_id": self.token_id,
            "user_id": self.user_id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "role": self.role.value,
            "token_type": "Bearer",
        }


@dataclass
class Favorite:
    favorite_id: str = field(default_factory=_id)
    user_id: str = ""
    vehicle_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {"favorite_id": self.favorite_id, "user_id": self.user_id, "vehicle_id": self.vehicle_id, "created_at": self.created_at}


@dataclass
class SavedSearch:
    search_id: str = field(default_factory=_id)
    user_id: str = ""
    name: str = ""
    criteria: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {"search_id": self.search_id, "user_id": self.user_id, "name": self.name, "criteria": dict(self.criteria), "created_at": self.created_at}


@dataclass
class GarageVehicle:
    garage_id: str = field(default_factory=_id)
    user_id: str = ""
    vehicle_id: str = ""
    vin: str = ""
    make: str = ""
    model: str = ""
    year: int = 0
    service_records: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "garage_id": self.garage_id,
            "user_id": self.user_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "service_records": list(self.service_records),
            "created_at": self.created_at,
        }


@dataclass
class TestDriveBooking:
    booking_id: str = field(default_factory=_id)
    user_id: str = ""
    customer_id: str = ""
    vehicle_id: str = ""
    dealer_id: str = ""
    scheduled_at: float = field(default_factory=_ts)
    status: str = "scheduled"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "vehicle_id": self.vehicle_id,
            "dealer_id": self.dealer_id,
            "scheduled_at": self.scheduled_at,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class TradeInRequest:
    request_id: str = field(default_factory=_id)
    user_id: str = ""
    customer_id: str = ""
    vin: str = ""
    make: str = ""
    model: str = ""
    year: int = 0
    mileage_km: int = 0
    estimated_value: float = 0.0
    status: str = "pending"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "vin": self.vin,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "mileage_km": self.mileage_km,
            "estimated_value": self.estimated_value,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class OfferRequest:
    request_id: str = field(default_factory=_id)
    user_id: str = ""
    customer_id: str = ""
    vehicle_id: str = ""
    dealer_id: str = ""
    proposed_amount: float = 0.0
    status: str = "pending"
    offer_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "vehicle_id": self.vehicle_id,
            "dealer_id": self.dealer_id,
            "proposed_amount": self.proposed_amount,
            "status": self.status,
            "offer_id": self.offer_id,
            "created_at": self.created_at,
        }


@dataclass
class PartnerConnection:
    connection_id: str = field(default_factory=_id)
    partner_id: str = ""
    partner_type: str = "dealer"
    name: str = ""
    api_key_hash: str = ""
    webhook_url: str = ""
    is_active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "partner_id": self.partner_id,
            "partner_type": self.partner_type,
            "name": self.name,
            "webhook_url": self.webhook_url,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class PortalNotification:
    notification_id: str = field(default_factory=_id)
    user_id: str = ""
    channel: str = "push"
    title: str = ""
    body: str = ""
    read: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "channel": self.channel,
            "title": self.title,
            "body": self.body,
            "read": self.read,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(32)
