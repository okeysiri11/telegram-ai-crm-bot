"""Billing Suite facade — Sprint 18.2."""

from __future__ import annotations

from typing import Any

from applications.finance_enterprise.billing.ai_finance import AIFinancialIntelligence
from applications.finance_enterprise.billing.cashflow import CashFlowIntelligence
from applications.finance_enterprise.billing.invoices import InvoiceManagement
from applications.finance_enterprise.billing.payables import AccountsPayable
from applications.finance_enterprise.billing.quotations import QuotationManagement
from applications.finance_enterprise.billing.receivables import AccountsReceivable
from applications.finance_enterprise.billing.services import BillingDashboard, BillingKnowledge
from applications.finance_enterprise.billing.tax import TaxEngine
from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


class BillingSuite:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.invoices = InvoiceManagement(self.store)
        self.quotations = QuotationManagement(self.store)
        self.receivables = AccountsReceivable(self.store)
        self.payables = AccountsPayable(self.store)
        self.tax = TaxEngine(self.store)
        self.cashflow = CashFlowIntelligence(self.store)
        self.ai = AIFinancialIntelligence(self.store)
        self.knowledge = BillingKnowledge(self.store)
        self.dashboard = BillingDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        inv_tpl = self.invoices.create_template(name="Standard Invoice")
        quote_tpl = self.quotations.create_template(name="Standard Quotation")

        quote = self.quotations.create(
            customer_ref="cust:acme", amount=10000, template_id=quote_tpl["template_id"]
        )
        self.quotations.approve(quotation_id=quote["quotation_id"], approver="sales_manager")
        converted = self.quotations.convert_to_invoice(
            quotation_id=quote["quotation_id"], invoices=self.invoices
        )

        proforma = self.invoices.create_invoice(
            customer_ref="cust:acme",
            amount=2500,
            invoice_type="proforma",
            template_id=inv_tpl["template_id"],
        )
        recurring = self.invoices.create_invoice(
            customer_ref="cust:acme",
            amount=1200,
            invoice_type="recurring",
            recurrence="monthly",
            tax_amount=240,
        )
        issued = self.invoices.issue(invoice_id=converted["invoice_id"])
        cn = self.invoices.credit_note(invoice_id=issued["invoice_id"], amount=100, reason="goodwill")
        dn = self.invoices.debit_note(invoice_id=issued["invoice_id"], amount=50, reason="shipping")

        ar = self.receivables.open_receivable(
            customer_ref="cust:acme",
            invoice_id=issued["invoice_id"],
            amount=issued["total"],
        )
        aging = self.receivables.aging(customer_ref="cust:acme")
        col = self.receivables.collect(receivable_id=ar["receivable_id"], step="reminder")
        alloc = self.receivables.allocate(
            receivable_id=ar["receivable_id"], amount=1000, payment_ref="PMT-1"
        )
        overdue_ar = self.receivables.open_receivable(
            customer_ref="cust:late", invoice_id=proforma["invoice_id"], amount=2500
        )
        self.receivables.mark_overdue(receivable_id=overdue_ar["receivable_id"])

        bill = self.payables.register_bill(
            vendor_ref="vend:global", amount=4500, due_on="2026-08-15", description="Ops supplies"
        )
        sch = self.payables.schedule_payment(bill_id=bill["bill_id"], schedule_at="2026-08-10")
        ap_apr = self.payables.approve(bill_id=bill["bill_id"], approver="controller")
        liab = self.payables.liabilities()
        vrec = self.payables.reconcile_statement(vendor_ref="vend:global", statement_total=4500)

        vat = self.tax.register_tax(code="VAT20", name="VAT 20%", rate=0.20, tax_type="vat")
        sales = self.tax.register_tax(code="ST8", name="Sales Tax 8%", rate=0.08, tax_type="sales")
        calc = self.tax.calculate(taxable_amount=10000, rate=0.20, tax_type="vat")
        rule = self.tax.add_rule(code="VAT20", jurisdiction="EU", rate=0.20)
        trep = self.tax.report(period="2026-Q3")
        tsum = self.tax.summary()

        rcpt = self.cashflow.expected_receipts(
            amount=9000, due_on="2026-08-01", source_ref=ar["receivable_id"]
        )
        epay = self.cashflow.expected_payments(
            amount=4500, due_on="2026-08-10", source_ref=bill["bill_id"]
        )
        cash_fc = self.cashflow.forecast(horizon_days=30, kind="cash")
        col_fc = self.cashflow.forecast(horizon_days=45, kind="collection")
        liq_fc = self.cashflow.forecast(horizon_days=60, kind="liquidity")

        late = self.ai.insight(
            insight_type="late_payment", subject="cust:late", score=0.81, detail="High late risk"
        )
        rec = self.ai.insight(
            insight_type="collection_recommendation",
            subject=overdue_ar["receivable_id"],
            score=0.77,
        )
        risk = self.ai.insight(insight_type="cash_flow_risk", subject="30d", score=0.55)
        anomaly = self.ai.insight(
            insight_type="invoice_anomaly", subject=issued["invoice_id"], score=0.2
        )
        revenue = self.ai.insight(insight_type="revenue_forecast", subject="2026-Q3", score=0.72)
        nl = self.ai.nl_summary(audience="cfo")

        self.knowledge.publish(base="invoice", key=issued["invoice_id"], payload={"total": issued["total"]})
        self.knowledge.publish(base="receivable", key=ar["receivable_id"], payload={"outstanding": ar["outstanding"]})
        self.knowledge.publish(base="payable", key=bill["bill_id"], payload={"amount": bill["amount"]})
        self.knowledge.publish(base="tax", key=vat["tax_id"], payload={"rate": vat["rate"]})
        self.knowledge.publish(base="cashflow", key=cash_fc["forecast_id"], payload={"net": cash_fc["net"]})

        dash_i = self.dashboard.render(dashboard_type="invoice")
        dash_r = self.dashboard.render(dashboard_type="receivables")
        dash_p = self.dashboard.render(dashboard_type="payables")
        dash_t = self.dashboard.render(dashboard_type="tax")
        dash_c = self.dashboard.render(dashboard_type="cashflow")

        return {
            "bootstrap": True,
            "invoice_template_id": inv_tpl["template_id"],
            "quote_template_id": quote_tpl["template_id"],
            "quotation_id": quote["quotation_id"],
            "converted_invoice_id": converted["invoice_id"],
            "proforma_id": proforma["invoice_id"],
            "recurring_id": recurring["invoice_id"],
            "credit_note_id": cn["credit_note_id"],
            "debit_note_id": dn["debit_note_id"],
            "receivable_id": ar["receivable_id"],
            "aging_id": aging["aging_id"],
            "collection_id": col["collection_id"],
            "allocation_id": alloc["allocation_id"],
            "overdue_receivable_id": overdue_ar["receivable_id"],
            "bill_id": bill["bill_id"],
            "schedule_id": sch["schedule_id"],
            "ap_approval_id": ap_apr["approval_id"],
            "liability_id": liab["liability_id"],
            "vendor_recon_id": vrec["reconciliation_id"],
            "vat_id": vat["tax_id"],
            "sales_tax_id": sales["tax_id"],
            "tax_calc_id": calc["calculation_id"],
            "tax_rule_id": rule["rule_id"],
            "tax_report_id": trep["report_id"],
            "tax_summary_id": tsum["summary_id"],
            "receipt_id": rcpt["receipt_id"],
            "expected_payment_id": epay["payment_id"],
            "cash_forecast_id": cash_fc["forecast_id"],
            "collection_forecast_id": col_fc["forecast_id"],
            "liquidity_forecast_id": liq_fc["forecast_id"],
            "late_insight_id": late["insight_id"],
            "collection_insight_id": rec["insight_id"],
            "risk_insight_id": risk["insight_id"],
            "anomaly_insight_id": anomaly["insight_id"],
            "revenue_insight_id": revenue["insight_id"],
            "nl_summary_id": nl["insight_id"],
            "dashboard_invoice_id": dash_i["dashboard_id"],
            "dashboard_receivables_id": dash_r["dashboard_id"],
            "dashboard_payables_id": dash_p["dashboard_id"],
            "dashboard_tax_id": dash_t["dashboard_id"],
            "dashboard_cashflow_id": dash_c["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "invoices": self.invoices.status(),
            "quotations": self.quotations.status(),
            "receivables": self.receivables.status(),
            "payables": self.payables.status(),
            "tax": self.tax.status(),
            "cashflow": self.cashflow.status(),
            "ai": self.ai.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


billing = BillingSuite()
