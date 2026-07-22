"""Agro Finance Suite facade — Sprint 14.6."""

from __future__ import annotations

from typing import Any

from applications.agro_enterprise.agro_finance.exchange import CommodityExchange, ContractManagement
from applications.agro_enterprise.agro_finance.finance import (
    AgriculturalFinance,
    CropInsurance,
    MarketIntelligence,
    RiskIntelligence,
)
from applications.agro_enterprise.agro_finance.services import AgroFinanceDashboard, AgroFinanceKnowledge
from applications.agro_enterprise.config import DEFAULT_CONFIG
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store


class AgroFinanceSuite:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.exchange = CommodityExchange(self.store)
        self.contracts = ContractManagement(self.store)
        self.finance = AgriculturalFinance(self.store)
        self.insurance = CropInsurance(self.store)
        self.risk = RiskIntelligence(self.store)
        self.market = MarketIntelligence(self.store)
        self.dashboard = AgroFinanceDashboard(self.store)
        self.knowledge = AgroFinanceKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        wheat = self.exchange.register_commodity(symbol="WHEAT", name="Milling Wheat", unit="t")
        corn = self.exchange.register_commodity(symbol="CORN", name="Yellow Corn", unit="t")
        buy = self.exchange.place_order(
            commodity_id=wheat["commodity_id"], side="buy", trade_type="spot", quantity=1000, price=245, party="MillCo"
        )
        sell = self.exchange.place_order(
            commodity_id=wheat["commodity_id"], side="sell", trade_type="forward", quantity=1000, price=248, party="FarmCo"
        )
        self.exchange.place_order(
            commodity_id=corn["commodity_id"], side="buy", trade_type="auction", quantity=500, price=205, party="FeedCo"
        )
        trade = self.exchange.execute_trade(buy_order_id=buy["order_id"], sell_order_id=sell["order_id"])
        depth = self.exchange.market_depth(wheat["commodity_id"])

        ctr = self.contracts.create_contract(
            contract_type="export", party="Cairo Mills", commodity="wheat", tons=5000, value=1_275_000
        )
        self.contracts.e_sign(ctr["contract_id"], signer="exporter@desk")
        self.contracts.advance_lifecycle(ctr["contract_id"], status="active")
        self.contracts.vault_document(contract_id=ctr["contract_id"], title="Export Contract PDF")

        farm_id = "farm_bootstrap"
        budget = self.finance.create_budget(farm_id=farm_id, year=2026, revenue=900000, costs=620000)
        self.finance.cash_flow(farm_id=farm_id, inflow=120000, outflow=85000)
        self.finance.cost_entry(farm_id=farm_id, category="fertilizer", amount=45000)
        self.finance.credit(farm_id=farm_id, limit=250000, utilized=80000)
        loan = self.finance.loan(farm_id=farm_id, principal=150000, rate_pct=7.5, term_months=36)
        self.finance.subsidy(farm_id=farm_id, program="EU-CAP", amount=22000)
        self.finance.grant(farm_id=farm_id, program="Irrigation Upgrade", amount=35000)

        insurer = self.insurance.register_insurer(name="AgroProtect")
        policy = self.insurance.create_policy(
            insurer_id=insurer["insurer_id"],
            farm_id=farm_id,
            crop="wheat",
            coverage=500000,
            premium=18000,
        )
        cov = self.insurance.coverage_calc(hectares=220, yield_t_ha=5.2, price=240, coverage_pct=0.75)
        self.insurance.risk_score(farm_id=farm_id, weather=0.4, market=0.3, production=0.35)
        claim = self.insurance.claim(policy_id=policy["policy_id"], amount=45000, damage_pct=28)

        for rtype, sev in (("weather", 0.55), ("market", 0.4), ("production", 0.35), ("financial", 0.3)):
            self.risk.assess(risk_type=rtype, entity_id=farm_id, severity=sev)
        warn = self.risk.early_warning(entity_id=farm_id, signal="drought_index", severity=0.62)

        self.market.publish_price(commodity="wheat", price=242, market="local")
        self.market.publish_price(commodity="wheat", price=246, market="export")
        self.market.supply_demand(commodity="wheat", supply_t=80000, demand_t=76000)
        fc = self.market.forecast(commodity="wheat", horizon_days=30)
        self.market.export_analytics(region="MENA", commodity="wheat", tons=12000, value=3_000_000)
        insight = self.market.trading_insight(commodity="wheat")

        for rtype, key in (
            ("financial", budget["budget_id"]),
            ("commodity", wheat["commodity_id"]),
            ("contract", ctr["contract_id"]),
            ("insurance", policy["policy_id"]),
            ("risk", warn["warning_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="finance")
        return {
            "bootstrap": True,
            "commodity_id": wheat["commodity_id"],
            "trade_id": trade["trade_id"],
            "contract_id": ctr["contract_id"],
            "budget_id": budget["budget_id"],
            "loan_id": loan["loan_id"],
            "policy_id": policy["policy_id"],
            "claim_id": claim["claim_id"],
            "coverage_calc_id": cov["calc_id"],
            "warning_id": warn["warning_id"],
            "forecast_id": fc["forecast_id"],
            "insight_id": insight["insight_id"],
            "best_bid": depth["price_discovery"]["best_bid"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "exchange": self.exchange.status(),
            "contracts": self.contracts.status(),
            "finance": self.finance.status(),
            "insurance": self.insurance.status(),
            "risk": self.risk.status(),
            "market": self.market.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


agro_finance = AgroFinanceSuite()
