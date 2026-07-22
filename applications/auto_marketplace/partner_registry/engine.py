# Partner Registry — dealers, service, transport, insurance, banks, gov, export, fleet.

from __future__ import annotations

from applications.auto_marketplace.enterprise.models import NetworkPartner, PartnerKind
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class PartnerRegistryEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def register(self, partner: NetworkPartner) -> NetworkPartner:
        if not partner.name:
            raise ValidationError("name is required")
        return self._store.network_partners.save(partner.partner_id, partner)

    def get(self, partner_id: str) -> NetworkPartner:
        item = self._store.network_partners.get(partner_id)
        if item is None:
            raise NotFoundError("NetworkPartner", partner_id)
        return item

    def list_partners(self, *, kind: str = "", country: str = "") -> list[NetworkPartner]:
        items = self._store.network_partners.list_all()
        if kind:
            items = [p for p in items if p.kind.value == kind]
        if country:
            items = [p for p in items if p.country.upper() == country.upper()]
        return items

    def metrics(self) -> dict:
        return {
            "partners": self._store.network_partners.count(),
            "kinds": [k.value for k in PartnerKind],
        }


partner_registry_engine = PartnerRegistryEngine()
