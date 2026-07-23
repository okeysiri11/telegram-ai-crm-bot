"""Technical Analysis Suite facade — Sprint 16.1."""

from __future__ import annotations

from typing import Any

from applications.crypto_enterprise.config import DEFAULT_CONFIG
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store
from applications.crypto_enterprise.technical_analysis.analysis import (
    ChartAnalysis,
    PatternRecognition,
    TechnicalIndicators,
)
from applications.crypto_enterprise.technical_analysis.services import (
    AITechnicalIntelligence,
    TechnicalDashboard,
    TechnicalKnowledge,
)
from applications.crypto_enterprise.technical_analysis.tradingview import MarketCharts, TradingViewIntegration


class TechnicalAnalysisSuite:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.tradingview = TradingViewIntegration(self.store)
        self.charts = MarketCharts(self.store)
        self.indicators = TechnicalIndicators(self.store)
        self.structures = ChartAnalysis(self.store)
        self.patterns = PatternRecognition(self.store)
        self.ai = AITechnicalIntelligence(self.store)
        self.dashboard = TechnicalDashboard(self.store)
        self.knowledge = TechnicalKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        tv = self.tradingview.connect_api(account="enterprise-trader")
        wl = self.tradingview.sync_watchlist(name="Core", symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
        chart_sync = self.tradingview.sync_chart(symbol="BTCUSDT", timeframe="1h")
        self.tradingview.set_timeframe(chart_id=chart_sync["sync_id"], timeframe="4h")
        drawing = self.tradingview.sync_drawing(
            chart_id=chart_sync["sync_id"],
            drawing_type="trendline",
            payload={"from": 66500, "to": 69000},
        )
        alert = self.tradingview.create_alert(symbol="BTCUSDT", condition="cross_above", price=70000)
        multi = self.tradingview.multi_chart(layout="2x2", symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"])

        candle = self.charts.create(symbol="BTCUSDT", chart_type="candlestick", timeframe="1h")
        self.charts.create(symbol="BTCUSDT", chart_type="heikin_ashi", timeframe="4h")
        self.charts.create(symbol="ETHUSDT", chart_type="line", timeframe="1d")
        self.charts.create(symbol="BTCUSDT", chart_type="area", timeframe="1h")
        self.charts.create(symbol="BTCUSDT", chart_type="volume", timeframe="1h")
        mtf = self.charts.multi_timeframe(symbol="BTCUSDT", timeframes=["15m", "1h", "4h", "1d"])
        self.charts.playback(
            chart_id=candle["chart_id"],
            from_ts="2026-07-01T00:00:00Z",
            to_ts="2026-07-20T00:00:00Z",
        )

        for ind in (
            "sma",
            "ema",
            "macd",
            "rsi",
            "stoch_rsi",
            "bollinger",
            "vwap",
            "atr",
            "adx",
            "ichimoku",
            "parabolic_sar",
            "supertrend",
        ):
            self.indicators.compute(indicator=ind, symbol="BTCUSDT", timeframe="1h")

        for structure in (
            "support",
            "resistance",
            "trendline",
            "channel",
            "triangle",
            "flag",
            "wedge",
            "breakout",
        ):
            self.structures.detect(structure=structure, symbol="BTCUSDT")

        for pattern in (
            "head_shoulders",
            "double_top",
            "double_bottom",
            "cup_handle",
            "ascending_triangle",
            "descending_triangle",
            "bull_flag",
            "bear_flag",
        ):
            self.patterns.recognize(pattern=pattern, symbol="BTCUSDT", timeframe="4h")
        candle_pat = self.patterns.recognize(
            pattern="candlestick",
            symbol="BTCUSDT",
            timeframe="1h",
            candle_pattern="engulfing_bullish",
        )

        trend = self.ai.trend_strength(symbol="BTCUSDT", score=0.72)
        self.ai.momentum(symbol="BTCUSDT", rsi=58.4)
        self.ai.volatility(symbol="BTCUSDT", atr_pct=2.4)
        conf = self.ai.confluence(symbol="BTCUSDT", indicators=["ema", "rsi", "macd", "supertrend"])
        self.ai.multi_timeframe_confirm(symbol="BTCUSDT", timeframes=["1h", "4h", "1d"])
        signal = self.ai.signal_confidence(symbol="BTCUSDT", side="long", confidence=0.81)
        setup = self.ai.trade_setup(symbol="BTCUSDT", entry=68100, stop=66500, target=72000)

        for rtype, key in (
            ("technical", candle["chart_id"]),
            ("indicator", "rsi"),
            ("pattern", candle_pat["pattern_id"]),
            ("tradingview", tv["connection_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="trading")
        return {
            "bootstrap": True,
            "tv_connection_id": tv["connection_id"],
            "watchlist_id": wl["watchlist_id"],
            "chart_sync_id": chart_sync["sync_id"],
            "drawing_id": drawing["drawing_id"],
            "alert_id": alert["alert_id"],
            "multi_chart_id": multi["layout_id"],
            "chart_id": candle["chart_id"],
            "mtf_id": mtf["analysis_id"],
            "trend_id": trend["analysis_id"],
            "confluence_id": conf["analysis_id"],
            "signal_id": signal["signal_id"],
            "setup_id": setup["setup_id"],
            "pattern_id": candle_pat["pattern_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "tradingview": self.tradingview.status(),
            "charts": self.charts.status(),
            "indicators": self.indicators.status(),
            "structures": self.structures.status(),
            "patterns": self.patterns.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


technical_analysis = TechnicalAnalysisSuite()
