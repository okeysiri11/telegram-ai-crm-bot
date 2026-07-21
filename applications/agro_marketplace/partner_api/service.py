# Partner API — connection registry and partner operations.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.agro_marketplace.partner_api.connectors import PartnerConnectors, partner_connectors
from applications.agro_marketplace.portal.events import PartnerConnectedEvent
from applications.agro_marketplace.portal.models import PartnerConnection, PartnerType
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class PartnerAPIService:
    def __init__(
        self,
        store: AgroStore | None = None,
        connectors: PartnerConnectors | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self._store = store or agro_store
        self.connectors = connectors or partner_connectors
        self._ecosystem = ecosystem or ecosystem_bridge

    async def connect(self, connection: PartnerConnection) -> PartnerConnection:
        if not connection.partner_name:
            raise ValidationError("partner_name is required")
        self._ecosystem.check_governance(
            "partner_connect",
            {"partner_type": connection.partner_type.value, "name": connection.partner_name},
        )
        connection.status = "connected"
        saved = self._store.partner_connections.save(connection.connection_id, connection)
        await publish(
            PartnerConnectedEvent(
                connection_id=saved.connection_id,
                partner_type=saved.partner_type.value,
                partner_name=saved.partner_name,
            )
        )
        return saved

    def list_connections(self, *, partner_type: PartnerType | None = None) -> list[PartnerConnection]:
        items = self._store.partner_connections.list_all()
        if partner_type:
            items = [c for c in items if c.partner_type == partner_type]
        return items

    def get(self, connection_id: str) -> PartnerConnection:
        connection = self._store.partner_connections.get(connection_id)
        if connection is None:
            raise NotFoundError("PartnerConnection", connection_id)
        return connection

    def invoke(self, partner_type: PartnerType | str, action: str, **kwargs):
        key = PartnerType(partner_type) if isinstance(partner_type, str) else partner_type
        mapping = {
            PartnerType.BANK: lambda: self.connectors.bank_transfer(**kwargs),
            PartnerType.INSURANCE: lambda: self.connectors.insurance_quote(**kwargs),
            PartnerType.LOGISTICS: lambda: self.connectors.logistics_book(**kwargs),
            PartnerType.GOVERNMENT: lambda: self.connectors.government_permit(**kwargs),
            PartnerType.LABORATORY: lambda: self.connectors.laboratory_submit(**kwargs),
            PartnerType.ERP: lambda: self.connectors.erp_sync(**kwargs),
            PartnerType.MARKETPLACE: lambda: self.connectors.marketplace_list(**kwargs),
        }
        if key not in mapping:
            raise ValidationError(f"unsupported partner type: {key}")
        # action reserved for future multi-action partners
        _ = action
        return mapping[key]()


partner_api_service = PartnerAPIService()
