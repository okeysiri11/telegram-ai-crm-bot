# Partner Network Engine — ports, lines, forwarders, rails, fleets, etc.

from __future__ import annotations

from applications.port_erp.enterprise.models import NetworkPartner, PartnerType
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class PartnerEngine:
    """Register and discover global port network partners."""

    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def partner_types(self) -> list[str]:
        return [p.value for p in PartnerType]

    def register(self, partner: NetworkPartner) -> NetworkPartner:
        if not partner.name:
            raise ValidationError("partner name is required")
        return self._store.network_partners.save(partner.partner_id, partner)

    def get(self, partner_id: str) -> NetworkPartner:
        partner = self._store.network_partners.get(partner_id)
        if partner is None:
            raise NotFoundError("partner", partner_id)
        return partner

    def list_partners(self, partner_type: str | None = None) -> list[NetworkPartner]:
        items = self._store.network_partners.list_all()
        if partner_type:
            items = [p for p in items if p.partner_type.value == partner_type]
        return items

    def discover(self, *, capability: str = "", region: str = "") -> list[NetworkPartner]:
        results = [p for p in self.list_partners() if p.is_active]
        if region:
            results = [p for p in results if p.region.lower() == region.lower() or p.country.lower() == region.lower()]
        if capability:
            results = [p for p in results if capability in p.capabilities]
        return sorted(results, key=lambda p: (-p.reliability_score, p.risk_score))


partner_engine = PartnerEngine()
