# Contract Engine — commercial contracts with shipping lines, forwarders, etc.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.finance.events import ContractActivatedEvent
from applications.port_erp.finance.models import CommercialContract, ContractPartyType, ContractStatus
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class ContractEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def party_types(self) -> list[str]:
        return [p.value for p in ContractPartyType]

    def create(self, contract: CommercialContract) -> CommercialContract:
        if not contract.title:
            raise ValidationError("title is required")
        if not contract.party_id and not contract.party_name:
            raise ValidationError("party_id or party_name is required")
        return self._store.commercial_contracts.save(contract.contract_id, contract)

    def get(self, contract_id: str) -> CommercialContract:
        item = self._store.commercial_contracts.get(contract_id)
        if item is None:
            raise NotFoundError("CommercialContract", contract_id)
        return item

    def list_contracts(
        self,
        *,
        party_type: ContractPartyType | None = None,
        status: ContractStatus | None = None,
    ) -> list[CommercialContract]:
        items = self._store.commercial_contracts.list_all()
        if party_type:
            items = [c for c in items if c.party_type == party_type]
        if status:
            items = [c for c in items if c.status == status]
        return items

    async def activate(self, contract_id: str) -> CommercialContract:
        contract = self.get(contract_id)
        contract.status = ContractStatus.ACTIVE
        saved = self._store.commercial_contracts.save(contract_id, contract)
        await publish(
            ContractActivatedEvent(
                contract_id=contract_id,
                party_type=saved.party_type.value,
                party_id=saved.party_id,
            )
        )
        return saved

    def suspend(self, contract_id: str) -> CommercialContract:
        contract = self.get(contract_id)
        contract.status = ContractStatus.SUSPENDED
        return self._store.commercial_contracts.save(contract_id, contract)


contract_engine = ContractEngine()
