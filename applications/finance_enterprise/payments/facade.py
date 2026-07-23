"""Payments Suite facade — Sprint 18.1."""

from __future__ import annotations

from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.payments.banking import Banking
from applications.finance_enterprise.payments.cash import CashManagement
from applications.finance_enterprise.payments.controls import FinancialControls
from applications.finance_enterprise.payments.payments import PaymentEngine
from applications.finance_enterprise.payments.processing import PaymentProcessing
from applications.finance_enterprise.payments.services import PaymentsDashboard, PaymentsKnowledge
from applications.finance_enterprise.payments.wallets import DigitalWallets
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


class PaymentsSuite:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.banking = Banking(self.store)
        self.wallets = DigitalWallets(self.store)
        self.payments = PaymentEngine(self.store)
        self.cash = CashManagement(self.store)
        self.processing = PaymentProcessing(self.store)
        self.controls = FinancialControls(self.store)
        self.knowledge = PaymentsKnowledge(self.store)
        self.dashboard = PaymentsDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        bank = self.banking.register_bank(
            name="Bidex National Bank", country="US", bic="BIDEXUS33", swift="BIDEXUS33"
        )
        acct = self.banking.register_account(
            bank_id=bank["bank_id"],
            account_name="Operating Account",
            iban="US00BIDEX0001001",
            currency="USD",
        )
        self.banking.set_iban(bank_account_id=acct["bank_account_id"], iban="US00 BIDEX 0001 001")
        self.banking.set_swift(bank_id=bank["bank_id"], swift="BIDEXUS33XXX")
        ver = self.banking.verify_account(bank_account_id=acct["bank_account_id"])
        stmt = self.banking.import_statement(
            bank_account_id=acct["bank_account_id"],
            period="2026-07",
            lines=[{"memo": "Opening", "amount": 250000}],
        )

        ent_wal = self.wallets.create_wallet(owner_ref="org:bidex", wallet_type="enterprise")
        cust_wal = self.wallets.create_wallet(owner_ref="cust:acme", wallet_type="customer", currency="USD")
        vend_wal = self.wallets.create_wallet(owner_ref="vend:global", wallet_type="vendor", currency="EUR")
        multi_wal = self.wallets.create_wallet(owner_ref="org:bidex", wallet_type="multi_currency", currency="USD")
        self.wallets.credit(wallet_id=ent_wal["wallet_id"], amount=50000, memo="seed")
        self.wallets.debit(wallet_id=ent_wal["wallet_id"], amount=1000, memo="ops")
        wh = self.wallets.credit(wallet_id=cust_wal["wallet_id"], amount=2500, memo="top-up")

        internal = self.payments.create_payment(
            payment_type="internal",
            amount=1000,
            from_ref=ent_wal["wallet_id"],
            to_ref=cust_wal["wallet_id"],
            external_key="INT-1001",
        )
        incoming = self.payments.create_payment(
            payment_type="incoming", amount=5000, to_ref=acct["bank_account_id"]
        )
        outgoing = self.payments.create_payment(
            payment_type="outgoing", amount=1200, from_ref=acct["bank_account_id"], to_ref="vend:global"
        )
        scheduled = self.payments.create_payment(
            payment_type="scheduled",
            amount=800,
            from_ref=ent_wal["wallet_id"],
            schedule_at="2026-08-01",
        )
        recurring = self.payments.create_payment(
            payment_type="recurring",
            amount=300,
            from_ref=ent_wal["wallet_id"],
            recurrence="monthly",
        )
        bulk = self.payments.bulk(
            payments=[
                {"payment_type": "outgoing", "amount": 100, "to_ref": "vend:a", "external_key": "B-1"},
                {"payment_type": "outgoing", "amount": 200, "to_ref": "vend:b", "external_key": "B-2"},
            ]
        )
        self.payments.update_status(payment_id=incoming["payment_id"], status="completed")

        reg = self.cash.open_register(name="HQ Cash Desk", branch="HQ", opening_balance=5000)
        self.cash.operate(register_id=reg["register_id"], operation="in", amount=500, memo="sale")
        self.cash.operate(register_id=reg["register_id"], operation="petty", amount=50, memo="supplies")
        recon = self.cash.reconcile(register_id=reg["register_id"], counted_balance=5450)
        flow = self.cash.track_flow(register_id=reg["register_id"])
        branch = self.cash.branch_account(branch="NYC", name="NYC Till")

        auth = self.processing.authorize(payment_id=outgoing["payment_id"], authorized_by="treasury")
        apr = self.processing.approve(payment_id=outgoing["payment_id"], approver="cfo")
        val = self.processing.validate_transaction(payment_id=outgoing["payment_id"])
        failed = self.payments.create_payment(
            payment_type="outgoing", amount=50, from_ref=ent_wal["wallet_id"], external_key="FAIL-1"
        )
        self.payments.update_status(payment_id=failed["payment_id"], status="failed")
        rec = self.processing.recover_failed(payment_id=failed["payment_id"])
        ntf = self.processing.notify(payment_id=outgoing["payment_id"], message="Payment approved")

        lim = self.controls.set_limit(role="accountant", max_amount=10000)
        perm = self.controls.grant(role="treasury", permission="authorize_payment")
        mtx = self.controls.approval_rule(min_amount=5000, required_role="cfo")
        aud = self.controls.audit(action="payments.bootstrap", actor="system")
        fraud = self.controls.fraud_flag(
            payment_id=failed["payment_id"], reason="retry pattern", severity="low"
        )

        self.knowledge.publish(base="payment", key=outgoing["payment_id"], payload={"amount": 1200})
        self.knowledge.publish(base="wallet", key=ent_wal["wallet_id"], payload={"type": "enterprise"})
        self.knowledge.publish(base="bank", key=bank["bank_id"], payload={"name": bank["name"]})
        self.knowledge.publish(base="cash", key=reg["register_id"], payload={"branch": "HQ"})
        self.knowledge.publish(base="transaction", key=wh["history_id"], payload={"amount": 2500})

        dash_p = self.dashboard.render(dashboard_type="payments")
        dash_w = self.dashboard.render(dashboard_type="wallets")
        dash_b = self.dashboard.render(dashboard_type="banking")
        dash_c = self.dashboard.render(dashboard_type="cash")

        return {
            "bootstrap": True,
            "bank_id": bank["bank_id"],
            "bank_account_id": acct["bank_account_id"],
            "verification_id": ver["verification_id"],
            "statement_id": stmt["statement_id"],
            "enterprise_wallet_id": ent_wal["wallet_id"],
            "customer_wallet_id": cust_wal["wallet_id"],
            "vendor_wallet_id": vend_wal["wallet_id"],
            "multi_wallet_id": multi_wal["wallet_id"],
            "internal_payment_id": internal["payment_id"],
            "incoming_payment_id": incoming["payment_id"],
            "outgoing_payment_id": outgoing["payment_id"],
            "scheduled_payment_id": scheduled["payment_id"],
            "recurring_payment_id": recurring["payment_id"],
            "bulk_id": bulk["bulk_id"],
            "register_id": reg["register_id"],
            "reconciliation_id": recon["reconciliation_id"],
            "flow_id": flow["flow_id"],
            "branch_account_id": branch["branch_account_id"],
            "authorization_id": auth["authorization_id"],
            "approval_id": apr["approval_id"],
            "validation_id": val["validation_id"],
            "recovery_id": rec["recovery_id"],
            "notification_id": ntf["notification_id"],
            "limit_id": lim["limit_id"],
            "permission_id": perm["permission_id"],
            "matrix_id": mtx["rule_id"],
            "audit_id": aud["audit_id"],
            "fraud_id": fraud["flag_id"],
            "dashboard_payments_id": dash_p["dashboard_id"],
            "dashboard_wallets_id": dash_w["dashboard_id"],
            "dashboard_banking_id": dash_b["dashboard_id"],
            "dashboard_cash_id": dash_c["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "banking": self.banking.status(),
            "wallets": self.wallets.status(),
            "payments": self.payments.status(),
            "cash": self.cash.status(),
            "processing": self.processing.status(),
            "controls": self.controls.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


payments = PaymentsSuite()
