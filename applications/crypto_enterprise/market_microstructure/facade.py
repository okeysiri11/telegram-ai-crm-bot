"""Market Microstructure Suite facade — Sprint 16.2."""

from __future__ import annotations

from typing import Any

from applications.crypto_enterprise.config import DEFAULT_CONFIG
from applications.crypto_enterprise.market_microstructure.derivatives import (
    DerivativesIntelligence,
    LiquidationIntelligence,
    LiquidityIntelligence,
)
from applications.crypto_enterprise.market_microstructure.order_flow import (
    OrderBookIntelligence,
    TradeFlowAnalysis,
)
from applications.crypto_enterprise.market_microstructure.services import (
    AIMarketInterpretation,
    MicrostructureDashboard,
    MicrostructureKnowledge,
)
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


class MarketMicrostructureSuite:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.order_book = OrderBookIntelligence(self.store)
        self.trade_flow = TradeFlowAnalysis(self.store)
        self.derivatives = DerivativesIntelligence(self.store)
        self.liquidations = LiquidationIntelligence(self.store)
        self.liquidity = LiquidityIntelligence(self.store)
        self.ai = AIMarketInterpretation(self.store)
        self.dashboard = MicrostructureDashboard(self.store)
        self.knowledge = MicrostructureKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        book = self.order_book.snapshot(symbol="BTCUSDT")
        self.order_book.depth(symbol="BTCUSDT", levels=25)
        self.order_book.bid_ask(symbol="BTCUSDT", bid=68000, ask=68010)
        self.order_book.heatmap(symbol="BTCUSDT")
        imb = self.order_book.imbalance(symbol="BTCUSDT", bid_volume=150, ask_volume=120)
        self.order_book.large_order(symbol="BTCUSDT", side="buy", size=85, price=67990)
        self.order_book.iceberg(symbol="BTCUSDT", side="sell", visible=5, estimated_total=40)
        self.order_book.spoofing(symbol="BTCUSDT", side="buy", size=200, cancelled_pct=0.92)

        ts = self.trade_flow.time_and_sales(symbol="BTCUSDT", price=68005, size=2.5, side="buy")
        self.trade_flow.classify(symbol="BTCUSDT", trade_class="aggressive", size=2.5)
        self.trade_flow.pressure(symbol="BTCUSDT", buy_volume=420, sell_volume=380)
        self.trade_flow.volume_delta(symbol="BTCUSDT", delta=40)
        cvd = self.trade_flow.cvd(symbol="BTCUSDT", cumulative=1250)
        self.trade_flow.aggressive(symbol="BTCUSDT", side="buy", size=12)
        self.trade_flow.large_trade(symbol="BTCUSDT", side="sell", size=55, price=68020)
        self.trade_flow.analytics(symbol="BTCUSDT")

        oi = self.derivatives.open_interest(symbol="BTCUSDT", oi=1.2e9, change_pct=2.4)
        self.derivatives.funding_rate(symbol="BTCUSDT", rate=0.00012)
        self.derivatives.long_short_ratio(symbol="BTCUSDT", long_pct=54, short_pct=46)
        self.derivatives.basis(symbol="BTCUSDT", spot=68000, futures=68120)
        self.derivatives.futures_premium(symbol="BTCUSDT", premium_pct=0.18)
        self.derivatives.options_overview(symbol="BTCUSDT", put_call_ratio=0.92, iv=48.5)
        self.derivatives.expiration_calendar(
            symbol="BTCUSDT",
            expiries=["2026-07-25", "2026-08-01", "2026-08-29"],
        )

        long_liq = self.liquidations.liquidation(symbol="BTCUSDT", side="long", size=12.4, price=67500)
        self.liquidations.liquidation(symbol="BTCUSDT", side="short", size=8.1, price=69200)
        self.liquidations.heatmap(symbol="BTCUSDT")
        self.liquidations.cluster(symbol="BTCUSDT", price=67000, size=45, side="long")
        cascade = self.liquidations.cascade(symbol="BTCUSDT", levels=4, total_size=120)
        self.liquidations.alert(symbol="BTCUSDT", side="long", size=20, price=66800)

        zone = self.liquidity.zone(symbol="BTCUSDT", price_low=66500, price_high=67000, strength=0.81)
        self.liquidity.support_liquidity(symbol="BTCUSDT", price=66500, size=90)
        self.liquidity.resistance_liquidity(symbol="BTCUSDT", price=69500, size=75)
        self.liquidity.stop_hunt(symbol="BTCUSDT", direction="below", swept_price=66480)
        self.liquidity.market_maker(symbol="BTCUSDT", activity_score=0.72)
        self.liquidity.absorption(symbol="BTCUSDT", side="buy", size=30)

        structure = self.ai.market_structure(symbol="BTCUSDT", structure="bullish_continuation", score=0.71)
        self.ai.institutional(symbol="BTCUSDT", intensity=0.66)
        self.ai.whale(symbol="BTCUSDT", size_usd=4_200_000, side="buy")
        self.ai.momentum_shift(symbol="BTCUSDT", from_bias="neutral", to_bias="long")
        self.ai.trend_continuation(symbol="BTCUSDT", probability=0.68)
        self.ai.reversal(symbol="BTCUSDT", probability=0.28)
        bias = self.ai.trade_bias(symbol="BTCUSDT", bias="long", confidence=0.74)
        conf = self.ai.confidence_score(
            symbol="BTCUSDT",
            score=0.76,
            drivers=["order_imbalance", "cvd", "funding", "oi"],
        )

        for rtype, key in (
            ("microstructure", book["book_id"]),
            ("order_book", imb["imbalance_id"]),
            ("derivatives", oi["oi_id"]),
            ("liquidity", zone["zone_id"]),
            ("trade_flow", ts["trade_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="order_flow")
        return {
            "bootstrap": True,
            "book_id": book["book_id"],
            "imbalance_id": imb["imbalance_id"],
            "trade_id": ts["trade_id"],
            "cvd_id": cvd["cvd_id"],
            "oi_id": oi["oi_id"],
            "long_liq_id": long_liq["liquidation_id"],
            "cascade_id": cascade["cascade_id"],
            "zone_id": zone["zone_id"],
            "structure_id": structure["analysis_id"],
            "bias_id": bias["bias_id"],
            "confidence_id": conf["score_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "order_book": self.order_book.status(),
            "trade_flow": self.trade_flow.status(),
            "derivatives": self.derivatives.status(),
            "liquidations": self.liquidations.status(),
            "liquidity": self.liquidity.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


market_microstructure = MarketMicrostructureSuite()
