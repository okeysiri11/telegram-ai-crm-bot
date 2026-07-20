# Contract Engine — purchase, sale, trade-in, dealer agreements.

from __future__ import annotations

import time

from events.publisher import publish

from applications.auto_marketplace.finance.ai_assistant import FinanceAIAssistant, finance_ai_assistant
from applications.auto_marketplace.finance.events import ContractSignedEvent
from applications.auto_marketplace.finance.models import (
    Contract,
    ContractStatus,
    ContractType,
    PurchaseAgreement,
    SaleAgreement,
)
from applications.auto_marketplace.finance.security import FinanceSecurity, finance_security
from applications.auto_marketplace.finance.workflow_bridge import FinanceWorkflowBridge, finance_workflow_bridge
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ContractService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        ai: FinanceAIAssistant | None = None,
        security: FinanceSecurity | None = None,
        workflow: FinanceWorkflowBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._ai = ai or finance_ai_assistant
        self._security = security or finance_security
        self._workflow = workflow or finance_workflow_bridge

    async def create(self, contract: Contract) -> Contract:
        analysis = await self._ai.analyze_contract(contract)
        contract.terms["risk_analysis"] = analysis
        saved = self._store.contracts.save(contract.contract_id, contract)
        self._security.audit(action="create", actor_id="system", resource_type="contract", resource_id=contract.contract_id)
        return saved

    async def create_purchase_agreement(self, agreement: PurchaseAgreement) -> PurchaseAgreement:
        agreement.contract_type = ContractType.PURCHASE
        agreement.title = agreement.title or "Purchase Agreement"
        return await self.create(agreement)  # type: ignore[return-value]

    async def create_sale_agreement(self, agreement: SaleAgreement) -> SaleAgreement:
        agreement.contract_type = ContractType.SALE
        agreement.title = agreement.title or "Sale Agreement"
        return await self.create(agreement)  # type: ignore[return-value]

    async def create_trade_in_contract(self, contract: Contract) -> Contract:
        contract.contract_type = ContractType.TRADE_IN
        contract.title = contract.title or "Trade-In Agreement"
        return await self.create(contract)

    async def create_dealer_agreement(self, contract: Contract) -> Contract:
        contract.contract_type = ContractType.DEALER
        contract.title = contract.title or "Dealer Agreement"
        return await self.create(contract)

    def get(self, contract_id: str) -> Contract:
        contract = self._store.contracts.get(contract_id)
        if contract is None:
            raise NotFoundError("Contract", contract_id)
        return contract

    def list_contracts(
        self,
        *,
        customer_id: str = "",
        dealer_id: str = "",
        contract_type: str = "",
    ) -> list[Contract]:
        items = self._store.contracts.list_all()
        if customer_id:
            items = [c for c in items if c.customer_id == customer_id]
        if dealer_id:
            items = [c for c in items if c.dealer_id == dealer_id]
        if contract_type:
            items = [c for c in items if c.contract_type.value == contract_type]
        return items

    async def submit_for_signature(self, contract_id: str, *, approver_id: str = "legal") -> Contract:
        contract = self.get(contract_id)
        contract.status = ContractStatus.PENDING_SIGNATURE
        workflow_id = await self._workflow.contract_approval(contract_id, approver_id)
        contract.terms["approval_workflow_id"] = workflow_id
        self._store.contracts.save(contract_id, contract)
        return contract

    async def sign(self, contract_id: str, *, signed_by: str) -> Contract:
        contract = self.get(contract_id)
        contract.status = ContractStatus.SIGNED
        contract.signed_at = time.time()
        contract.signed_by = signed_by
        self._store.contracts.save(contract_id, contract)
        self._security.audit(actor_id=signed_by, action="sign", resource_type="contract", resource_id=contract_id)
        await publish(
            ContractSignedEvent(
                contract_id=contract_id,
                contract_type=contract.contract_type.value,
                customer_id=contract.customer_id,
                amount=contract.amount,
            )
        )
        return contract

    def activate(self, contract_id: str) -> Contract:
        contract = self.get(contract_id)
        contract.status = ContractStatus.ACTIVE
        self._store.contracts.save(contract_id, contract)
        return contract

    def terminate(self, contract_id: str, *, reason: str = "") -> Contract:
        contract = self.get(contract_id)
        contract.status = ContractStatus.TERMINATED
        contract.terms["termination_reason"] = reason
        self._store.contracts.save(contract_id, contract)
        return contract

    async def analyze(self, contract_id: str) -> dict:
        return await self._ai.analyze_contract(self.get(contract_id))


contract_service = ContractService()
