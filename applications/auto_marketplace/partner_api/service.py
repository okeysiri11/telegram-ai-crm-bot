# Partner API — dealer, insurance, financing, inspection, logistics integrations.

from __future__ import annotations

import hashlib
import secrets
from typing import Any

from events.publisher import publish

from applications.auto_marketplace.authentication.models import PartnerConnection, generate_token
from applications.auto_marketplace.customer_portal.events import PartnerConnectedEvent
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class PartnerAPIService:
    PARTNER_TYPES = ("dealer", "insurance", "financing", "inspection", "logistics")

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    async def connect_partner(self, *, name: str, partner_type: str, webhook_url: str = "") -> tuple[PartnerConnection, str]:
        if partner_type not in self.PARTNER_TYPES:
            partner_type = "dealer"
        api_key = generate_token()
        conn = PartnerConnection(
            partner_id=secrets.token_hex(8),
            partner_type=partner_type,
            name=name,
            api_key_hash=hashlib.sha256(api_key.encode()).hexdigest(),
            webhook_url=webhook_url,
        )
        self._store.partner_connections.save(conn.connection_id, conn)
        await publish(PartnerConnectedEvent(connection_id=conn.connection_id, partner_id=conn.partner_id, partner_type=partner_type))
        return conn, api_key

    def validate_api_key(self, api_key: str) -> PartnerConnection | None:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        for conn in self._store.partner_connections.list_all():
            if conn.api_key_hash == key_hash and conn.is_active:
                return conn
        return None

    def list_connections(self, *, partner_type: str = "") -> list[PartnerConnection]:
        items = self._store.partner_connections.list_all()
        if partner_type:
            items = [c for c in items if c.partner_type == partner_type]
        return items

    async def insurance_quote(self, vehicle_id: str, customer_id: str) -> dict[str, Any]:
        return {"vehicle_id": vehicle_id, "customer_id": customer_id, "monthly_premium": 120.0, "provider": "partner_insurance"}

    async def financing_quote(self, amount: float, term_months: int = 60) -> dict[str, Any]:
        rate = 0.059
        monthly = amount * (rate / 12) / (1 - (1 + rate / 12) ** (-term_months)) if amount else 0
        return {"amount": amount, "term_months": term_months, "apr": rate, "monthly_payment": round(monthly, 2)}

    async def schedule_inspection(self, vehicle_id: str, dealer_id: str) -> dict[str, Any]:
        return {"vehicle_id": vehicle_id, "dealer_id": dealer_id, "status": "scheduled", "inspection_type": "pre_delivery"}

    async def schedule_logistics(self, deal_id: str, destination: str) -> dict[str, Any]:
        return {"deal_id": deal_id, "destination": destination, "status": "scheduled", "carrier": "partner_logistics"}

    async def dispatch_webhook(self, connection_id: str, event: str, payload: dict) -> dict[str, Any]:
        conn = self._store.partner_connections.get(connection_id)
        if conn is None:
            return {"error": "connection_not_found"}
        return {"webhook_url": conn.webhook_url, "event": event, "payload": payload, "dispatched": True}


partner_api_service = PartnerAPIService()
