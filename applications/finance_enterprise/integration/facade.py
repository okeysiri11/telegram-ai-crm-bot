"""Integration Suite facade — Sprint 18.7."""

from __future__ import annotations

from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.integration.ai_enterprise import AIEnterpriseFinance
from applications.finance_enterprise.integration.event_bus import FinancialEventBus
from applications.finance_enterprise.integration.intelligence import EnterpriseFinancialIntelligence
from applications.finance_enterprise.integration.platforms import (
    agro_integration,
    automotive_integration,
    crypto_integration,
    legal_integration,
    port_integration,
)
from applications.finance_enterprise.integration.services import IntegrationDashboard, IntegrationKnowledge
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


class IntegrationSuite:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.event_bus = FinancialEventBus(self.store)
        self.automotive = automotive_integration(self.store, self.event_bus)
        self.agro = agro_integration(self.store, self.event_bus)
        self.port = port_integration(self.store, self.event_bus)
        self.crypto = crypto_integration(self.store, self.event_bus)
        self.legal = legal_integration(self.store, self.event_bus)
        self.intelligence = EnterpriseFinancialIntelligence(self.store)
        self.ai = AIEnterpriseFinance(self.store)
        self.knowledge = IntegrationKnowledge(self.store)
        self.dashboard = IntegrationDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        for name, plat in (
            ("vehicle.sale", "automotive"),
            ("crop.sale", "agro"),
            ("shipping.invoice", "port"),
            ("crypto.settlement", "crypto"),
            ("legal.billing", "legal"),
        ):
            self.event_bus.register_event_type(name=name, platform=plat)

        auto_sale = self.automotive.operate(
            operation="vehicle_sales", amount=45000, reference="VIN-1001"
        )
        auto_pay = self.automotive.operate(
            operation="customer_payment", amount=45000, reference="PAY-A1"
        )
        auto_svc = self.automotive.operate(
            operation="service_invoice", amount=1200, reference="SVC-88"
        )
        auto_parts = self.automotive.operate(
            operation="parts_valuation", amount=85000, reference="PARTS-Q2"
        )
        auto_war = self.automotive.operate(
            operation="warranty_tracking", amount=500, reference="WAR-12"
        )
        auto_deal = self.automotive.operate(
            operation="dealer_settlement", amount=12000, reference="DLR-9"
        )

        agro_crop = self.agro.operate(operation="crop_sales", amount=220000, reference="HARVEST-1")
        agro_wh = self.agro.operate(operation="warehouse_valuation", amount=310000, reference="WH-A")
        agro_sup = self.agro.operate(operation="supplier_payments", amount=45000, reference="SUP-22")
        agro_cost = self.agro.operate(operation="harvest_cost", amount=78000, reference="HC-1")
        agro_exp = self.agro.operate(operation="export_settlement", amount=150000, reference="EXP-AG")
        agro_sub = self.agro.operate(operation="subsidy_tracking", amount=25000, reference="SUB-9")

        port_inv = self.port.operate(operation="shipping_invoice", amount=18000, reference="SHP-1")
        port_cargo = self.port.operate(operation="cargo_cost", amount=9200, reference="CG-1")
        port_fee = self.port.operate(operation="terminal_fee", amount=3500, reference="TERM-1")
        port_log = self.port.operate(operation="logistics_tracking", amount=4100, reference="LOG-1")
        port_doc = self.port.operate(operation="export_docs_billing", amount=800, reference="DOC-1")
        port_set = self.port.operate(operation="port_settlement", amount=15000, reference="PORT-SET")

        cry_set = self.crypto.operate(operation="digital_asset_settlement", amount=100000, reference="DA-1")
        cry_otc = self.crypto.operate(operation="otc_accounting", amount=50000, reference="OTC-1")
        cry_tre = self.crypto.operate(operation="treasury_sync", amount=250000, reference="TRE-1")
        cry_wal = self.crypto.operate(operation="wallet_sync", amount=125000, reference="WAL-1")
        cry_ex = self.crypto.operate(operation="exchange_settlement", amount=75000, reference="EX-1")
        cry_st = self.crypto.operate(operation="stablecoin_accounting", amount=200000, reference="USDT-1")

        leg_bill = self.legal.operate(operation="contract_billing", amount=15000, reference="CTR-1")
        leg_fee = self.legal.operate(operation="legal_fee", amount=8000, reference="FEE-1")
        leg_court = self.legal.operate(operation="court_cost", amount=2500, reference="CRT-1")
        leg_comp = self.legal.operate(operation="compliance_cost", amount=4200, reference="CMP-1")
        leg_lic = self.legal.operate(operation="license_fee", amount=6000, reference="LIC-1")
        leg_exp = self.legal.operate(operation="expense_allocation", amount=11000, reference="LEX-1")

        evt = self.store.int_events.list_all()[0]
        replay = self.event_bus.replay(event_id=evt["event_id"])
        monitor = self.event_bus.monitor()

        an_prof = self.intelligence.analyze(
            analytic_type="cross_platform_profitability",
            subject="Group",
            value=520000,
            platforms=["automotive", "agro", "port", "crypto", "legal"],
        )
        an_cf = self.intelligence.analyze(
            analytic_type="unified_cash_flow", subject="Enterprise", value=380000
        )
        an_rev = self.intelligence.analyze(
            analytic_type="enterprise_revenue", subject="FY2026", value=1_800_000
        )
        an_cost = self.intelligence.analyze(
            analytic_type="enterprise_cost", subject="FY2026", value=1_100_000
        )
        an_dep = self.intelligence.analyze(
            analytic_type="dependency_mapping", subject="Cash rails", value=0.72
        )
        an_risk = self.intelligence.analyze(
            analytic_type="risk_correlation", subject="Platforms", value=0.41
        )
        dep1 = self.intelligence.map_dependency(
            from_platform="automotive", to_platform="finance_enterprise", dependency="sales_settlement", strength=0.9
        )
        dep2 = self.intelligence.map_dependency(
            from_platform="crypto", to_platform="finance_enterprise", dependency="treasury_sync", strength=0.85
        )

        ai_mon = self.ai.insight(insight_type="process_monitoring", subject="Event bus", score=0.8)
        ai_anom = self.ai.insight(insight_type="anomaly", subject="Agro export spike", score=0.65)
        ai_rec = self.ai.insight(insight_type="cross_platform_recommendation", subject="Cash pooling", score=0.88)
        ai_exe = self.ai.insight(insight_type="executive_insight", subject="Q2 outlook", score=0.84)
        ai_h = self.ai.health_score(subject="Bidex Enterprise", score=0.87)
        ai_nl = self.ai.nl_report(audience="board")

        self.knowledge.publish(base="integration", key=auto_sale["operation_id"], payload={"platform": "automotive"})
        self.knowledge.publish(base="event", key=evt["event_id"], payload={"kind": evt["event_kind"]})
        self.knowledge.publish(base="dependency", key=dep1["dependency_id"], payload={"from": "automotive"})
        self.knowledge.publish(base="analytics", key=an_prof["analytic_id"], payload={"type": "profitability"})
        self.knowledge.publish(base="finance", key=ai_h["insight_id"], payload={"health": 0.87})

        dash_ef = self.dashboard.render(dashboard_type="enterprise_finance")
        dash_cp = self.dashboard.render(dashboard_type="cross_platform")
        dash_op = self.dashboard.render(dashboard_type="operations")
        dash_rev = self.dashboard.render(dashboard_type="revenue")
        dash_exe = self.dashboard.render(dashboard_type="executive_integration")

        return {
            "bootstrap": True,
            "auto_sale_id": auto_sale["operation_id"],
            "auto_payment_id": auto_pay["operation_id"],
            "auto_service_id": auto_svc["operation_id"],
            "auto_parts_id": auto_parts["operation_id"],
            "auto_warranty_id": auto_war["operation_id"],
            "auto_dealer_id": auto_deal["operation_id"],
            "agro_crop_id": agro_crop["operation_id"],
            "agro_warehouse_id": agro_wh["operation_id"],
            "agro_supplier_id": agro_sup["operation_id"],
            "agro_harvest_id": agro_cost["operation_id"],
            "agro_export_id": agro_exp["operation_id"],
            "agro_subsidy_id": agro_sub["operation_id"],
            "port_invoice_id": port_inv["operation_id"],
            "port_cargo_id": port_cargo["operation_id"],
            "port_fee_id": port_fee["operation_id"],
            "port_logistics_id": port_log["operation_id"],
            "port_docs_id": port_doc["operation_id"],
            "port_settlement_id": port_set["operation_id"],
            "crypto_settlement_id": cry_set["operation_id"],
            "crypto_otc_id": cry_otc["operation_id"],
            "crypto_treasury_id": cry_tre["operation_id"],
            "crypto_wallet_id": cry_wal["operation_id"],
            "crypto_exchange_id": cry_ex["operation_id"],
            "crypto_stablecoin_id": cry_st["operation_id"],
            "legal_billing_id": leg_bill["operation_id"],
            "legal_fee_id": leg_fee["operation_id"],
            "legal_court_id": leg_court["operation_id"],
            "legal_compliance_id": leg_comp["operation_id"],
            "legal_license_id": leg_lic["operation_id"],
            "legal_expense_id": leg_exp["operation_id"],
            "replay_id": replay["replay_id"],
            "monitor_id": monitor["monitor_id"],
            "analytic_profitability_id": an_prof["analytic_id"],
            "analytic_cashflow_id": an_cf["analytic_id"],
            "analytic_revenue_id": an_rev["analytic_id"],
            "analytic_cost_id": an_cost["analytic_id"],
            "analytic_dependency_id": an_dep["analytic_id"],
            "analytic_risk_id": an_risk["analytic_id"],
            "dependency_auto_id": dep1["dependency_id"],
            "dependency_crypto_id": dep2["dependency_id"],
            "ai_monitor_id": ai_mon["insight_id"],
            "ai_anomaly_id": ai_anom["insight_id"],
            "ai_recommendation_id": ai_rec["insight_id"],
            "ai_executive_id": ai_exe["insight_id"],
            "ai_health_id": ai_h["insight_id"],
            "ai_nl_id": ai_nl["insight_id"],
            "dashboard_enterprise_id": dash_ef["dashboard_id"],
            "dashboard_cross_platform_id": dash_cp["dashboard_id"],
            "dashboard_operations_id": dash_op["dashboard_id"],
            "dashboard_revenue_id": dash_rev["dashboard_id"],
            "dashboard_executive_id": dash_exe["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "event_bus": self.event_bus.status(),
            "automotive": self.automotive.status(),
            "agro": self.agro.status(),
            "port": self.port.status(),
            "crypto": self.crypto.status(),
            "legal": self.legal.status(),
            "intelligence": self.intelligence.status(),
            "ai": self.ai.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


integration = IntegrationSuite()
