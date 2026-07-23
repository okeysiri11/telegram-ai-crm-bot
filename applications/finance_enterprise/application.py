"""FinanceEnterpriseApplication — Sprint 18.0 foundation (Bidex)."""

from __future__ import annotations

from typing import Any

from applications.finance_enterprise.architecture import FinancialArchitecture
from applications.finance_enterprise.config import DEFAULT_CONFIG, FinanceEnterpriseConfig
from applications.finance_enterprise.currency import MultiCurrency
from applications.finance_enterprise.finance_registry import FinanceRegistry
from applications.finance_enterprise.ledger import GeneralLedger
from applications.finance_enterprise.services import FinanceDashboard, FinanceKnowledge
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


class FinanceEnterpriseApplication:
    def __init__(
        self,
        *,
        config: FinanceEnterpriseConfig | None = None,
        store: FinanceEnterpriseStore | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or finance_enterprise_store
        self.registry = FinanceRegistry(self.store)
        self.ledger = GeneralLedger(self.store)
        self.currency = MultiCurrency(self.store)
        self.architecture = FinancialArchitecture(self.store)
        self.knowledge = FinanceKnowledge(self.store)
        self.dashboard = FinanceDashboard(self.store)

    def reset(self) -> None:
        self.store.reset()

    def bootstrap(self) -> dict[str, Any]:
        org = self.registry.register_organization(
            name="Bidex Holdings", jurisdiction="US-DE", registration_no="DE-FE-1001"
        )
        customer = self.registry.register_customer(
            name="Acme Trading LLC", organization_id=org["organization_id"], country="US"
        )
        vendor = self.registry.register_vendor(
            name="Global Supplies Inc", organization_id=org["organization_id"], country="US"
        )
        usd = self.registry.register_currency(code="USD", name="US Dollar")
        eur = self.registry.register_currency(code="EUR", name="Euro")
        gbp = self.registry.register_currency(code="GBP", name="British Pound")
        cash_fa = self.registry.register_financial_account(
            name="Operating Cash",
            account_code="BANK-001",
            currency="USD",
            organization_id=org["organization_id"],
        )
        cc = self.registry.register_cost_center(
            code="CC-FIN", name="Finance Ops", organization_id=org["organization_id"]
        )
        entity = self.registry.register_entity(
            name="Bidex Holdings", entity_type="organization", ref_id=org["organization_id"]
        )

        cash = self.ledger.add_account(code="1000", name="Cash", account_type="asset")
        ar = self.ledger.add_account(code="1100", name="Accounts Receivable", account_type="asset")
        ap = self.ledger.add_account(code="2000", name="Accounts Payable", account_type="liability")
        equity = self.ledger.add_account(code="3000", name="Owner Equity", account_type="equity")
        revenue = self.ledger.add_account(code="4000", name="Service Revenue", account_type="revenue")
        expense = self.ledger.add_account(code="5000", name="Operating Expense", account_type="expense")

        je = self.ledger.create_journal_entry(
            description="Seed capital and opening cash",
            reference="OPEN-001",
            lines=[
                {"account_code": "1000", "debit": 100000, "credit": 0},
                {"account_code": "3000", "debit": 0, "credit": 100000},
            ],
        )
        posted = self.ledger.post(journal_id=je["journal_id"])
        tb = self.ledger.trial_balance()

        base = self.currency.set_base_currency(code="USD")
        rate_eu = self.currency.register_rate(from_currency="USD", to_currency="EUR", rate=0.92)
        rate_gb = self.currency.register_rate(from_currency="USD", to_currency="GBP", rate=0.78)
        conv = self.currency.convert(amount=1000, from_currency="USD", to_currency="EUR")

        self.architecture.set_config(key="fiscal_year", value="2026")
        self.architecture.grant_permission(role="cfo", permission="approve_journals")
        self.architecture.grant_permission(role="accountant", permission="post_journals")
        evt = self.architecture.publish_event(
            event_type="finance.bootstrap",
            payload={"organization_id": org["organization_id"]},
        )
        audit = self.architecture.audit(
            action="bootstrap",
            actor="system",
            resource="finance_enterprise",
            detail="Sprint 18.0 foundation seed",
        )

        self.knowledge.publish(base="entity", key=org["organization_id"], payload={"name": org["name"]})
        self.knowledge.publish(base="account", key=cash["code"], payload={"name": cash["name"]})
        self.knowledge.publish(base="ledger", key=je["journal_id"], payload={"status": posted["status"]})
        self.knowledge.publish(base="currency", key=usd["code"], payload={"name": usd["name"]})
        self.knowledge.publish(base="finance", key="foundation", payload={"version": self.config.application_version})
        self.knowledge.relate(from_node=f"fe:entity:{org['organization_id']}", to_node=f"fe:account:{cash['code']}")
        self.knowledge.relate(from_node=f"fe:ledger:{je['journal_id']}", to_node=f"fe:account:{cash['code']}")
        self.knowledge.relate(from_node=f"fe:currency:{usd['code']}", to_node="fe:finance:foundation")

        dash = self.dashboard.render(dashboard_type="overview")
        return {
            "bootstrap": True,
            "organization_id": org["organization_id"],
            "customer_id": customer["customer_id"],
            "vendor_id": vendor["vendor_id"],
            "currency_usd_id": usd["currency_id"],
            "currency_eur_id": eur["currency_id"],
            "currency_gbp_id": gbp["currency_id"],
            "financial_account_id": cash_fa["account_id"],
            "cost_center_id": cc["cost_center_id"],
            "entity_id": entity["entity_id"],
            "coa_cash_id": cash["coa_id"],
            "coa_ar_id": ar["coa_id"],
            "coa_ap_id": ap["coa_id"],
            "coa_equity_id": equity["coa_id"],
            "coa_revenue_id": revenue["coa_id"],
            "coa_expense_id": expense["coa_id"],
            "journal_id": je["journal_id"],
            "posting_count": posted["posting_count"],
            "trial_balance_id": tb["trial_balance_id"],
            "base_currency_config": base["key"],
            "rate_eur_id": rate_eu["rate_id"],
            "rate_gbp_id": rate_gb["rate_id"],
            "conversion_id": conv["conversion_id"],
            "event_id": evt["event_id"],
            "audit_id": audit["audit_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": self.config.application_version,
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "enterprise_foundation": self.config.enterprise_foundation,
            "platform_dependency": self.config.platform_dependency,
            "ecosystem_dependency": self.config.ecosystem_dependency,
            "api_prefix": self.config.api_prefix,
            "finance_enterprise_foundation_ready": True,
            "general_ledger_ready": True,
            "financial_registry_ready": True,
            "multi_currency_ready": True,
            "financial_architecture_ready": True,
            "financial_knowledge_graph_ready": True,
            "engines": {
                "financial_registry": self.config.financial_registry,
                "general_ledger": self.config.general_ledger,
                "multi_currency": self.config.multi_currency,
                "financial_architecture": self.config.financial_architecture,
                "knowledge": self.config.knowledge,
                "analytics": self.config.analytics,
            },
            "registry": self.registry.status(),
            "ledger": self.ledger.status(),
            "currency": self.currency.status(),
            "architecture": self.architecture.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


finance_enterprise = FinanceEnterpriseApplication()
