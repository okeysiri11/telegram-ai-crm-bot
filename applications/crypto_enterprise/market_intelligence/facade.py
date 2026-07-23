"""Market Intelligence Suite facade — Sprint 16.3."""

from __future__ import annotations

from typing import Any

from applications.crypto_enterprise.config import DEFAULT_CONFIG
from applications.crypto_enterprise.market_intelligence.engines import (
    AICorrelationEngine,
    AIDecisionEngine,
    IntelligenceDashboard,
    IntelligenceKnowledge,
)
from applications.crypto_enterprise.market_intelligence.fundamentals import (
    FundamentalIntelligence,
    MacroIntelligence,
    SentimentIntelligence,
)
from applications.crypto_enterprise.market_intelligence.news_social import NewsIntelligence, SocialIntelligence
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


class MarketIntelligenceSuite:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.news = NewsIntelligence(self.store)
        self.social = SocialIntelligence(self.store)
        self.sentiment = SentimentIntelligence(self.store)
        self.fundamentals = FundamentalIntelligence(self.store)
        self.macro = MacroIntelligence(self.store)
        self.correlation = AICorrelationEngine(self.store)
        self.decision = AIDecisionEngine(self.store)
        self.dashboard = IntelligenceDashboard(self.store)
        self.knowledge = IntelligenceKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        news = self.news.aggregate(source="coindesk", headline="BTC ETF inflows accelerate")
        self.news.classify(news_id=news["news_id"], category="etf")
        breaking = self.news.breaking(headline="Fed holds rates — risk assets bid", severity=0.82)
        self.news.economic_calendar(events=[{"name": "CPI", "date": "2026-08-12"}])
        self.news.crypto_events(events=[{"name": "ETH Upgrade", "date": "2026-09-01"}])
        self.news.etf_news(ticker="IBIT", headline="Record weekly inflows")
        self.news.exchange_announcement(exchange="binance", title="New perpetual listings")
        self.news.project_announcement(project="Ethereum", title="Pectra follow-up")

        for source, handle in (
            ("x", "@whalealert"),
            ("telegram", "crypto_signals"),
            ("reddit", "r/Bitcoin"),
            ("youtube", "macro_desk"),
            ("discord", "alpha-room"),
        ):
            self.social.analyze_source(source=source, handle=handle, mentions=120, engagement=0.64)
        self.social.influencer(handle="@macrotrader", platform="x", followers=850000, influence_score=0.88)
        self.social.trending(topics=["BTC", "ETF", "Fed", "ETH"])
        self.social.hashtags(tags=["#Bitcoin", "#Crypto"], volume=42000)

        sent = self.sentiment.market_index(score=62)
        self.sentiment.fear_greed(value=58)
        self.sentiment.classify(text="Strong ETF bid into weakness", label="bullish", confidence=0.81)
        self.sentiment.history(points=[{"t": "2026-07-01", "score": 48}, {"t": "2026-07-20", "score": 62}])
        self.sentiment.trend(direction="up", strength=0.55)
        self.sentiment.regional(region="US", score=64, label="bullish")

        project = self.fundamentals.register_project(name="Bitcoin", symbol="BTC", category="store_of_value")
        self.fundamentals.token_fundamentals(symbol="BTC", market_cap=1.3e12, fdv=1.3e12, holders=50_000_000)
        self.fundamentals.unlock_calendar(symbol="SOL", unlocks=[{"date": "2026-08-01", "amount": 1.2e7}])
        self.fundamentals.tokenomics(symbol="ETH", circulating_pct=82.0, inflation_pct=0.5)
        self.fundamentals.developer_activity(symbol="ETH", commits_30d=420, contributors=180)
        self.fundamentals.github_activity(repo="ethereum/go-ethereum", stars=48000, forks=20000, open_issues=320)
        self.fundamentals.partnership(project="Chainlink", partner="SWIFT", kind="infrastructure")
        self.fundamentals.protocol_update(protocol="Ethereum", version="Pectra+", summary="UX and staking improvements")

        fed = self.macro.fed(title="FOMC Decision", scheduled_at="2026-07-30T18:00:00Z")
        self.macro.inflation(title="US CPI", scheduled_at="2026-08-12T12:30:00Z")
        self.macro.interest_rate(title="Fed Funds Path", scheduled_at="2026-07-30T18:00:00Z")
        self.macro.employment(title="NFP", scheduled_at="2026-08-07T12:30:00Z")
        self.macro.gdp(title="US GDP QoQ", scheduled_at="2026-07-30T12:30:00Z")
        self.macro.global_macro(title="ECB Policy", scheduled_at="2026-07-24T12:15:00Z")

        corr = self.correlation.correlate(
            correlation_type="news_price", symbol="BTCUSDT", coefficient=0.72, window="7d"
        )
        for ctype, coef in (
            ("sentiment_volume", 0.61),
            ("macro_market", -0.48),
            ("whale_price", 0.55),
            ("funding_trend", 0.33),
            ("oi_momentum", 0.58),
        ):
            self.correlation.correlate(correlation_type=ctype, symbol="BTCUSDT", coefficient=coef)

        summary = self.decision.market_summary(
            symbol="BTCUSDT",
            summary="ETF inflows and improving sentiment support a constructive short-term bias.",
        )
        self.decision.risk_level(symbol="BTCUSDT", level="medium", score=0.48)
        opp = self.decision.opportunity(symbol="BTCUSDT", score=71)
        self.decision.probabilities(symbol="BTCUSDT", bullish=0.58, bearish=0.27)
        self.decision.volatility_forecast(symbol="BTCUSDT", forecast_pct=3.2, horizon="7d")
        self.decision.outlook(
            symbol="BTCUSDT",
            horizon="short",
            bias="bullish",
            narrative="Dip-buying near support remains favored while ETF flow stays positive.",
        )
        self.decision.outlook(symbol="BTCUSDT", horizon="medium", bias="bullish", narrative="Macro path remains supportive.")
        self.decision.outlook(symbol="BTCUSDT", horizon="long", bias="neutral", narrative="Cycle maturity increases dispersion.")
        expl = self.decision.explain(
            symbol="BTCUSDT",
            explanation="News-price and sentiment-volume correlations align with a bullish short-term setup.",
        )

        for rtype, key in (
            ("intelligence", summary["summary_id"]),
            ("news", news["news_id"]),
            ("sentiment", sent["index_id"]),
            ("macro", fed["event_id"]),
            ("correlation", corr["correlation_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="ai_market")
        return {
            "bootstrap": True,
            "news_id": news["news_id"],
            "breaking_id": breaking["breaking_id"],
            "sentiment_id": sent["index_id"],
            "project_id": project["project_id"],
            "macro_id": fed["event_id"],
            "correlation_id": corr["correlation_id"],
            "summary_id": summary["summary_id"],
            "opportunity_id": opp["opportunity_id"],
            "explanation_id": expl["explanation_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "news": self.news.status(),
            "social": self.social.status(),
            "sentiment": self.sentiment.status(),
            "fundamentals": self.fundamentals.status(),
            "macro": self.macro.status(),
            "correlation": self.correlation.status(),
            "decision": self.decision.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


market_intelligence = MarketIntelligenceSuite()
