# Carrier Management Engine — carriers + contracts.

from __future__ import annotations

from applications.port_erp.companies.service import CompanyRegistry, company_registry
from applications.port_erp.multimodal.models import CarrierContract, TransportMode
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Carrier
from applications.port_erp.shared.store import PortStore, port_store


class CarrierManagementEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        companies: CompanyRegistry | None = None,
    ) -> None:
        self._store = store or port_store
        self._companies = companies or company_registry

    def register(self, carrier: Carrier) -> Carrier:
        return self._companies.register_carrier(carrier)

    def list_carriers(self, *, mode: str | None = None) -> list[Carrier]:
        items = self._store.carriers.list_all()
        if mode:
            items = [c for c in items if c.mode == mode]
        return items

    def get(self, carrier_id: str) -> Carrier:
        item = self._store.carriers.get(carrier_id)
        if item is None:
            raise NotFoundError("Carrier", carrier_id)
        return item

    def create_contract(self, contract: CarrierContract) -> CarrierContract:
        self.get(contract.carrier_id)
        if contract.rate_per_unit < 0:
            raise ValidationError("rate_per_unit must be non-negative")
        return self._store.carrier_contracts.save(contract.contract_id, contract)

    def list_contracts(self, *, carrier_id: str | None = None) -> list[CarrierContract]:
        items = self._store.carrier_contracts.list_all()
        if carrier_id:
            items = [c for c in items if c.carrier_id == carrier_id]
        return items

    def best_rate(self, *, mode: TransportMode | str, partner_id: str = "") -> CarrierContract | None:
        mode_value = mode.value if isinstance(mode, TransportMode) else mode
        contracts = [c for c in self.list_contracts() if c.mode.value == mode_value]
        if partner_id:
            contracts = [c for c in contracts if c.partner_id == partner_id] or contracts
        if not contracts:
            return None
        return sorted(contracts, key=lambda c: c.rate_per_unit)[0]


carrier_management_engine = CarrierManagementEngine()
