# Refund and settlement management.

from __future__ import annotations

import time

from events.publisher import publish

from applications.auto_marketplace.finance.events import RefundProcessedEvent, SettlementCompletedEvent
from applications.auto_marketplace.finance.models import DealerSettlement, Refund, RefundStatus, SettlementStatus, Transaction, TransactionType
from applications.auto_marketplace.finance.security import FinanceSecurity, finance_security
from applications.auto_marketplace.finance.workflow_bridge import FinanceWorkflowBridge, finance_workflow_bridge
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AccountingService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        security: FinanceSecurity | None = None,
        workflow: FinanceWorkflowBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._security = security or finance_security
        self._workflow = workflow or finance_workflow_bridge

    async def request_refund(self, *, payment_id: str, amount: float, reason: str = "", currency: str = "USD") -> Refund:
        refund = Refund(payment_id=payment_id, amount=amount, reason=reason, currency=currency)
        saved = self._store.refunds.save(refund.refund_id, refund)
        await self._workflow.refund_workflow(refund.refund_id, "finance-manager")
        self._security.audit(action="refund_request", actor_id="system", resource_type="refund", resource_id=refund.refund_id)
        return saved

    def get_refund(self, refund_id: str) -> Refund:
        refund = self._store.refunds.get(refund_id)
        if refund is None:
            raise NotFoundError("Refund", refund_id)
        return refund

    async def process_refund(self, refund_id: str) -> Refund:
        refund = self.get_refund(refund_id)
        refund.status = RefundStatus.PROCESSED
        refund.processed_at = time.time()
        txn = Transaction(
            transaction_type=TransactionType.REFUND,
            payment_id=refund.payment_id,
            amount=refund.amount,
            currency=refund.currency,
            reference=f"refund-{refund_id[:8]}",
        )
        self._store.transactions.save(txn.transaction_id, txn)
        saved = self._store.refunds.save(refund_id, refund)
        self._security.audit(action="refund_process", actor_id="system", resource_type="refund", resource_id=refund_id)
        await publish(RefundProcessedEvent(refund_id=refund_id, payment_id=refund.payment_id, amount=refund.amount))
        return saved

    def create_settlement(
        self,
        *,
        dealer_id: str,
        period_start: float,
        period_end: float,
        gross_amount: float,
        commission_total: float,
        payment_ids: list[str] | None = None,
        currency: str = "USD",
    ) -> DealerSettlement:
        settlement = DealerSettlement(
            dealer_id=dealer_id,
            period_start=period_start,
            period_end=period_end,
            gross_amount=gross_amount,
            commission_total=commission_total,
            net_amount=round(gross_amount - commission_total, 2),
            currency=currency,
            payment_ids=payment_ids or [],
        )
        return self._store.dealer_settlements.save(settlement.settlement_id, settlement)

    async def complete_settlement(self, settlement_id: str) -> DealerSettlement:
        settlement = self._store.dealer_settlements.get(settlement_id)
        if settlement is None:
            raise NotFoundError("DealerSettlement", settlement_id)
        settlement.status = SettlementStatus.COMPLETED
        saved = self._store.dealer_settlements.save(settlement_id, settlement)
        self._security.audit(action="settlement_complete", actor_id="system", resource_type="settlement", resource_id=settlement_id)
        await publish(
            SettlementCompletedEvent(
                settlement_id=settlement_id,
                dealer_id=settlement.dealer_id,
                net_amount=settlement.net_amount,
            )
        )
        return saved

    def ledger_summary(self) -> dict:
        payments = self._store.finance_payments.list_all()
        refunds = self._store.refunds.list_all()
        total_in = sum(p.amount for p in payments if p.status == "completed")
        total_out = sum(r.amount for r in refunds if r.status == RefundStatus.PROCESSED)
        return {"total_inflow": round(total_in, 2), "total_outflow": round(total_out, 2), "net": round(total_in - total_out, 2)}


accounting_service = AccountingService()
