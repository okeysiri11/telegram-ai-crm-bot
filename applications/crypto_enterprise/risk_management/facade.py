"""Risk Management Suite facade — Sprint 16.5."""

from __future__ import annotations

from typing import Any

from applications.crypto_enterprise.config import DEFAULT_CONFIG
from applications.crypto_enterprise.risk_management.intelligence import (
    AIRiskIntelligence,
    RiskDashboard,
    RiskKnowledge,
)
from applications.crypto_enterprise.risk_management.portfolio import (
    AdvancedRiskModels,
    PortfolioOptimization,
    TradeProtection,
)
from applications.crypto_enterprise.risk_management.sizing import PositionSizing, RiskAnalytics
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


class RiskManagementSuite:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.sizing = PositionSizing(self.store)
        self.analytics = RiskAnalytics(self.store)
        self.optimization = PortfolioOptimization(self.store)
        self.models = AdvancedRiskModels(self.store)
        self.protection = TradeProtection(self.store)
        self.ai = AIRiskIntelligence(self.store)
        self.dashboard = RiskDashboard(self.store)
        self.knowledge = RiskKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        portfolio_id = "pf_core_crypto"
        size = self.sizing.size(
            method="percentage",
            symbol="BTCUSDT",
            capital=250000,
            risk_pct=1.0,
            stop_distance=800,
        )
        for method in ("fixed", "atr", "kelly", "volatility", "max_exposure", "dynamic"):
            self.sizing.size(
                method=method,
                symbol="BTCUSDT",
                capital=250000,
                risk_pct=1.0,
                stop_distance=800,
                atr=650,
                volatility=2.4,
                max_exposure_pct=8,
            )

        trade_risk = self.analytics.risk_per_trade(symbol="BTCUSDT", risk_amount=2500, capital=250000)
        self.analytics.portfolio_risk(portfolio_id=portfolio_id, var_pct=3.2, exposure_pct=62)
        self.analytics.drawdown(portfolio_id=portfolio_id, current_dd=0.045, max_dd=0.12)
        self.analytics.loss_limit(period="daily", limit_pct=2.0, realized_pct=0.6)
        self.analytics.loss_limit(period="weekly", limit_pct=5.0, realized_pct=1.8)
        self.analytics.loss_limit(period="monthly", limit_pct=10.0, realized_pct=3.5)
        self.analytics.heatmap(portfolio_id=portfolio_id)

        alloc = self.optimization.asset_allocation(
            name="Core Risk Book",
            weights={"BTC": 45, "ETH": 30, "SOL": 15, "CASH": 10},
        )
        self.optimization.sector_allocation(
            name="Crypto Sectors",
            sectors={"L1": 50, "DeFi": 20, "Infrastructure": 20, "Cash": 10},
        )
        self.optimization.correlation_matrix(assets=["BTC", "ETH", "SOL"])
        self.optimization.diversification(score=0.72, holdings=4)
        self.optimization.rebalance(portfolio_id=portfolio_id, target={"BTC": 45, "ETH": 30, "SOL": 15, "CASH": 10})
        self.optimization.capital_efficiency(portfolio_id=portfolio_id, deployed_pct=88, idle_pct=12)

        var = self.models.var(portfolio_id=portfolio_id, confidence=0.95, var_pct=3.1)
        self.models.cvar(portfolio_id=portfolio_id, confidence=0.95, cvar_pct=4.6)
        self.models.monte_carlo(portfolio_id=portfolio_id, simulations=10000)
        self.models.stress_test(portfolio_id=portfolio_id, scenario="flash_crash", shock_pct=-20)
        self.models.scenario(portfolio_id=portfolio_id, name="risk_off", outcome="drawdown_controlled")
        self.models.tail_risk(portfolio_id=portfolio_id, tail_pct=4.2)

        self.protection.dynamic_stop(symbol="BTCUSDT", stop=66500, atr_mult=1.5)
        self.protection.adaptive_tp(symbol="BTCUSDT", targets=[70000, 72000, 75000])
        self.protection.trailing_stop(symbol="BTCUSDT", trail_pct=1.25)
        self.protection.breakeven(symbol="BTCUSDT", trigger_r=1.0)
        self.protection.partial_profit(
            symbol="BTCUSDT",
            levels=[{"pct": 30, "price": 70000}, {"pct": 30, "price": 72000}],
        )
        emergency = self.protection.emergency_exit(symbol="BTCUSDT", reason="daily_loss_limit_approaching")

        market = self.ai.market_risk_score(symbol="BTCUSDT", score=48)
        health = self.ai.portfolio_health(portfolio_id=portfolio_id, score=78)
        self.ai.capital_preservation(portfolio_id=portfolio_id, score=82)
        self.ai.exposure_recommendation(
            portfolio_id=portfolio_id,
            action="hold",
            rationale="Risk budget within limits; diversification healthy.",
        )
        self.ai.leverage_recommendation(
            symbol="BTCUSDT",
            max_leverage=2.0,
            rationale="Medium market risk score favors capped leverage.",
        )
        approval = self.ai.trade_approval(
            symbol="BTCUSDT",
            side="long",
            size=size["quantity"],
            risk_pct=1.0,
            approved=True,
        )
        warning = self.ai.warning(
            portfolio_id=portfolio_id,
            severity="info",
            message="Weekly loss utilization at 36% of limit.",
        )
        report = self.ai.report(
            portfolio_id=portfolio_id,
            narrative="Capital preservation is strong; VaR within policy and position sizing remains disciplined.",
        )

        for rtype, key in (
            ("risk", trade_risk["risk_id"]),
            ("portfolio", alloc["allocation_id"]),
            ("exposure", market["score_id"]),
            ("risk_model", var["var_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="risk")
        return {
            "bootstrap": True,
            "portfolio_id": portfolio_id,
            "sizing_id": size["sizing_id"],
            "trade_risk_id": trade_risk["risk_id"],
            "allocation_id": alloc["allocation_id"],
            "var_id": var["var_id"],
            "emergency_id": emergency["protection_id"],
            "market_score_id": market["score_id"],
            "health_id": health["health_id"],
            "approval_id": approval["approval_id"],
            "warning_id": warning["warning_id"],
            "report_id": report["report_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "sizing": self.sizing.status(),
            "analytics": self.analytics.status(),
            "optimization": self.optimization.status(),
            "models": self.models.status(),
            "protection": self.protection.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


risk_management = RiskManagementSuite()
