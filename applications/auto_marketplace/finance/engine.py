# FinanceEngine — unified documents, contracts & financial operations facade.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.accounting.service import AccountingService, accounting_service
from applications.auto_marketplace.billing.service import BillingService, billing_service
from applications.auto_marketplace.contracts.service import ContractService, contract_service
from applications.auto_marketplace.documents.engine import DocumentEngine, document_engine
from applications.auto_marketplace.finance.ai_assistant import FinanceAIAssistant, finance_ai_assistant
from applications.auto_marketplace.finance.security import FinanceSecurity, finance_security
from applications.auto_marketplace.finance.workflow_bridge import FinanceWorkflowBridge, finance_workflow_bridge
from applications.auto_marketplace.invoices.service import InvoiceService, invoice_service
from applications.auto_marketplace.payments.operations import PaymentOperationsService, payment_operations_service
from applications.auto_marketplace.receipts.service import ReceiptService, receipt_service
from applications.auto_marketplace.reports.service import ReportService, report_service
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.taxes.service import TaxService, tax_service


class FinanceEngine:
    """Enterprise Documents, Contracts & Financial Operations entry point."""

    def __init__(
        self,
        store: MarketplaceStore | None = None,
        documents: DocumentEngine | None = None,
        contracts: ContractService | None = None,
        payments: PaymentOperationsService | None = None,
        billing: BillingService | None = None,
        invoices: InvoiceService | None = None,
        receipts: ReceiptService | None = None,
        taxes: TaxService | None = None,
        accounting: AccountingService | None = None,
        reports: ReportService | None = None,
        ai: FinanceAIAssistant | None = None,
        security: FinanceSecurity | None = None,
        workflow: FinanceWorkflowBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self.documents = documents or document_engine
        self.contracts = contracts or contract_service
        self.payments = payments or payment_operations_service
        self.billing = billing or billing_service
        self.invoices = invoices or invoice_service
        self.receipts = receipts or receipt_service
        self.taxes = taxes or tax_service
        self.accounting = accounting or accounting_service
        self.reports = reports or report_service
        self.ai = ai or finance_ai_assistant
        self.security = security or finance_security
        self.workflow = workflow or finance_workflow_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            "documents": self._store.finance_documents.count(),
            "contracts": self._store.contracts.count(),
            "payments": self._store.finance_payments.count(),
            "invoices": self._store.finance_invoices.count(),
            "receipts": self._store.receipts.count(),
            "refunds": self._store.refunds.count(),
            "settlements": self._store.dealer_settlements.count(),
            "ledger": self.accounting.ledger_summary(),
        }


finance_engine = FinanceEngine()
