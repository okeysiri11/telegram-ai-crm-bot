"""Strategy Engine Suite facade — Sprint 16.4."""

from __future__ import annotations

from typing import Any

from applications.crypto_enterprise.config import DEFAULT_CONFIG
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store
from applications.crypto_enterprise.strategy_engine.backtesting import BacktestingEngine, PerformanceAnalytics
from applications.crypto_enterprise.strategy_engine.builder import StrategyBuilder
from applications.crypto_enterprise.strategy_engine.intelligence import (
    AIStrategyIntelligence,
    StrategyDashboard,
    StrategyKnowledge,
)
from applications.crypto_enterprise.strategy_engine.signals import PortfolioSimulation, SignalGeneration


class StrategyEngineSuite:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.builder = StrategyBuilder(self.store)
        self.backtesting = BacktestingEngine(self.store)
        self.performance = PerformanceAnalytics(self.store)
        self.signals = SignalGeneration(self.store)
        self.portfolio_sim = PortfolioSimulation(self.store)
        self.ai = AIStrategyIntelligence(self.store)
        self.dashboard = StrategyDashboard(self.store)
        self.knowledge = StrategyKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        visual = self.builder.create_visual(
            name="BTC Trend Canvas",
            nodes=[{"type": "indicator", "value": "ema_cross"}, {"type": "sentiment", "value": "bullish"}],
        )
        trend = self.builder.from_template(template="trend_follow", name="BTC Trend Follow", symbol="BTCUSDT")
        mr = self.builder.from_template(template="mean_reversion", name="ETH Mean Reversion", symbol="ETHUSDT")
        self.builder.add_rule(
            strategy_id=trend["strategy_id"],
            condition_type="indicator",
            expression="ema_20 > ema_50",
            timeframe="1h",
        )
        self.builder.add_rule(
            strategy_id=trend["strategy_id"],
            condition_type="volume",
            expression="volume > sma_volume_20",
            timeframe="1h",
        )
        self.builder.add_rule(
            strategy_id=trend["strategy_id"],
            condition_type="order_flow",
            expression="cvd_rising",
            timeframe="15m",
        )
        self.builder.add_rule(
            strategy_id=trend["strategy_id"],
            condition_type="sentiment",
            expression="fear_greed > 50",
            timeframe="1d",
        )
        self.builder.add_rule(
            strategy_id=trend["strategy_id"],
            condition_type="macro",
            expression="risk_on",
            timeframe="1d",
        )
        self.builder.add_rule(
            strategy_id=trend["strategy_id"],
            condition_type="market_structure",
            expression="higher_highs",
            timeframe="4h",
        )
        self.builder.multi_timeframe(
            strategy_id=trend["strategy_id"],
            timeframes=["15m", "1h", "4h"],
            logic="and",
        )

        self.backtesting.load_market_data(symbol="BTCUSDT", bars=5000, timeframe="1h")
        replay = self.backtesting.historical_replay(
            strategy_id=trend["strategy_id"],
            from_ts="2025-01-01T00:00:00Z",
            to_ts="2026-07-01T00:00:00Z",
            bars=5000,
        )
        bt = self.backtesting.run(
            strategy_id=trend["strategy_id"],
            from_ts="2025-01-01T00:00:00Z",
            to_ts="2026-07-01T00:00:00Z",
            capital=100000,
        )
        self.backtesting.walk_forward(strategy_id=trend["strategy_id"], windows=6)
        self.backtesting.monte_carlo(strategy_id=trend["strategy_id"], simulations=2000)
        self.backtesting.optimize(strategy_id=trend["strategy_id"], params={"ema_fast": 20, "ema_slow": 50})
        self.backtesting.compare(strategy_ids=[trend["strategy_id"], mr["strategy_id"]])
        self.backtesting.portfolio_backtest(
            strategy_ids=[trend["strategy_id"], mr["strategy_id"]],
            capital=250000,
        )
        perf = self.performance.compute(backtest_id=bt["backtest_id"])

        entry = self.signals.entry(
            strategy_id=trend["strategy_id"],
            symbol="BTCUSDT",
            side="long",
            price=68100,
            confidence=0.82,
        )
        self.signals.exit(strategy_id=trend["strategy_id"], symbol="BTCUSDT", price=72000, reason="take_profit")
        self.signals.take_profit(strategy_id=trend["strategy_id"], symbol="BTCUSDT", targets=[70000, 72000, 75000])
        self.signals.stop_loss(strategy_id=trend["strategy_id"], symbol="BTCUSDT", stop=66500)
        self.signals.trailing_stop(strategy_id=trend["strategy_id"], symbol="BTCUSDT", trail_pct=1.5)
        self.signals.scale_position(strategy_id=trend["strategy_id"], symbol="BTCUSDT", sizes=[0.4, 0.3, 0.3])

        alloc = self.portfolio_sim.allocate(name="Core Crypto Book", allocations={"BTC": 50, "ETH": 30, "SOL": 20})
        self.portfolio_sim.multi_asset(assets=["BTC", "ETH", "SOL"], capital=250000)
        self.portfolio_sim.exposure(long_pct=70, short_pct=10, cash_pct=20)
        self.portfolio_sim.correlation(assets=["BTC", "ETH"])
        self.portfolio_sim.diversification(score=0.68, holdings=3)

        eval_row = self.ai.evaluate(strategy_id=trend["strategy_id"], score=78)
        self.ai.detect_regime(symbol="BTCUSDT", regime="trending", confidence=0.77)
        self.ai.adaptive_select(
            symbol="BTCUSDT",
            strategy_ids=[trend["strategy_id"], mr["strategy_id"]],
            selected_id=trend["strategy_id"],
        )
        self.ai.optimize_strategy(strategy_id=trend["strategy_id"], improvement=0.12)
        self.ai.scenario(strategy_id=trend["strategy_id"], name="risk_off_shock", outcome="drawdown_contained")
        rec = self.ai.recommend(
            symbol="BTCUSDT",
            action="long",
            rationale="Trend and multi-timeframe confluence remain constructive.",
        )
        expl = self.ai.explain(
            strategy_id=trend["strategy_id"],
            explanation="EMA cross with volume and order-flow confirmation drives entries.",
        )
        self.ai.report(
            strategy_id=trend["strategy_id"],
            narrative="Backtest shows positive expectancy with controlled drawdown under trending regimes.",
        )

        for rtype, key in (
            ("strategy", trend["strategy_id"]),
            ("backtesting", bt["backtest_id"]),
            ("signal", entry["signal_id"]),
            ("performance", perf["performance_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="strategy")
        return {
            "bootstrap": True,
            "visual_id": visual["builder_id"],
            "strategy_id": trend["strategy_id"],
            "alt_strategy_id": mr["strategy_id"],
            "replay_id": replay["replay_id"],
            "backtest_id": bt["backtest_id"],
            "performance_id": perf["performance_id"],
            "entry_id": entry["signal_id"],
            "allocation_id": alloc["allocation_id"],
            "evaluation_id": eval_row["evaluation_id"],
            "recommendation_id": rec["recommendation_id"],
            "explanation_id": expl["explanation_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "builder": self.builder.status(),
            "backtesting": self.backtesting.status(),
            "performance": self.performance.status(),
            "signals": self.signals.status(),
            "portfolio_sim": self.portfolio_sim.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


strategy_engine = StrategyEngineSuite()
