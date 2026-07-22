# Finance domain facade — commercial management.

from __future__ import annotations

from typing import Any

from applications.port_erp.accounting.engine import AccountingEngine, accounting_engine
from applications.port_erp.billing.engine import BillingEngine, billing_engine
from applications.port_erp.budget.engine import BudgetEngine, budget_engine
from applications.port_erp.contracts.engine import ContractEngine, contract_engine
from applications.port_erp.currencies.engine import CurrencyEngine, TaxEngine, currency_engine, tax_engine
from applications.port_erp.customers.accounts import CustomerAccountEngine, customer_account_engine
from applications.port_erp.finance.engine import FinanceEngine, finance_engine
from applications.port_erp.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.port_erp.invoices.engine import InvoiceEngine, invoice_engine
from applications.port_erp.payments.engine import PaymentEngine, payment_engine
from applications.port_erp.profitability.engine import ProfitabilityEngine, profitability_engine
from applications.port_erp.suppliers.engine import SupplierEngine, supplier_engine
from applications.port_erp.tariffs.commercial import CommercialTariffEngine, commercial_tariff_engine


class FinanceDomainEngine:
    """Sprint 9.7 facade — finance, billing, contracts, accounting."""

    def __init__(
        self,
        finance: FinanceEngine | None = None,
        billing: BillingEngine | None = None,
        contracts: ContractEngine | None = None,
        tariffs: CommercialTariffEngine | None = None,
        invoices: InvoiceEngine | None = None,
        payments: PaymentEngine | None = None,
        accounting: AccountingEngine | None = None,
        accounts: CustomerAccountEngine | None = None,
        profitability: ProfitabilityEngine | None = None,
        budgets: BudgetEngine | None = None,
        suppliers: SupplierEngine | None = None,
        currencies: CurrencyEngine | None = None,
        taxes: TaxEngine | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self.finance = finance or finance_engine
        self.billing = billing or billing_engine
        self.contracts = contracts or contract_engine
        self.tariffs = tariffs or commercial_tariff_engine
        self.invoices = invoices or invoice_engine
        self.payments = payments or payment_engine
        self.accounting = accounting or accounting_engine
        self.accounts = accounts or customer_account_engine
        self.profitability = profitability or profitability_engine
        self.budgets = budgets or budget_engine
        self.suppliers = suppliers or supplier_engine
        self.currencies = currencies or currency_engine
        self.taxes = taxes or tax_engine
        self._platform = platform or platform_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            "tariffs": len(self.tariffs.list_tariffs()),
            "contracts": len(self.contracts.list_contracts()),
            "invoices": len(self.invoices.list_invoices()),
            "payments": len(self.payments.list_payments()),
            "journal_entries": len(self.accounting.journal()),
            "budgets": len(self.budgets.list_budgets()),
            "suppliers": len(self.suppliers.list_suppliers()),
            "customer_accounts": len(self.accounts.list_accounts()),
            "receivables": self.accounting.receivables(),
            "payables": self.accounting.payables(),
        }

    async def remember_snapshot(self) -> None:
        await self._platform.remember_context("finance:snapshot", self.metrics())


finance_domain_engine = FinanceDomainEngine()
