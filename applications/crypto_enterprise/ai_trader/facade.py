"""AI Trader Suite facade — Sprint 16.7."""

from __future__ import annotations

from typing import Any

from applications.crypto_enterprise.ai_trader.decision import AIDecisionCenter, AITradingAssistant
from applications.crypto_enterprise.ai_trader.explainability import (
    AIExplainability,
    AITraderDashboard,
    AITraderKnowledge,
    AlertCenter,
)
from applications.crypto_enterprise.ai_trader.recommendations import (
    ExecutiveDecisionSupport,
    PortfolioIntelligence,
    TradeRecommendationEngine,
)
from applications.crypto_enterprise.config import DEFAULT_CONFIG
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


class AITraderSuite:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.decision = AIDecisionCenter(self.store)
        self.assistant = AITradingAssistant(self.store)
        self.recommendations = TradeRecommendationEngine(self.store)
        self.portfolio_intel = PortfolioIntelligence(self.store)
        self.executive = ExecutiveDecisionSupport(self.store)
        self.explainability = AIExplainability(self.store)
        self.alerts = AlertCenter(self.store)
        self.dashboard = AITraderDashboard(self.store)
        self.knowledge = AITraderKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        factors = self.decision.multi_factor(
            symbol="BTCUSDT",
            scores={
                "technical": 0.72,
                "derivatives": 0.61,
                "onchain": 0.58,
                "news": 0.66,
                "sentiment": 0.63,
                "risk": 0.55,
            },
        )
        decision = self.decision.decide(
            symbol="BTCUSDT",
            bullish=0.58,
            bearish=0.24,
            confidence=0.76,
            risk="medium",
        )
        self.decision.scenario(
            symbol="BTCUSDT",
            name="continuation",
            outcome="grind_higher",
            probability=0.52,
        )
        self.decision.scenario(
            symbol="BTCUSDT",
            name="risk_off",
            outcome="mean_revert",
            probability=0.28,
        )
        opp = self.decision.rank_opportunity(
            symbol="BTCUSDT",
            score=78,
            thesis="ETF flow + constructive technical/on-chain confluence",
        )
        self.decision.rank_opportunity(symbol="ETHUSDT", score=71, thesis="Relative strength in L1 beta")
        self.decision.classify_risk(symbol="SOLUSDT", risk="high", rationale="Elevated unlock and volatility")

        chat = self.assistant.chat(
            topic="executive_summary",
            question="What is the executive market stance today?",
        )
        self.assistant.chat(topic="daily_briefing", question="Daily crypto briefing?")
        self.assistant.compare_assets(symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"], winner="BTCUSDT")
        briefing = self.assistant.briefing(
            briefing_type="executive",
            summary="Maintain core BTC exposure; favor high-confidence long setups with defined risk.",
        )
        self.assistant.briefing(
            briefing_type="daily",
            summary="Risk tone constructive; watch funding and whale exchange inflows.",
        )

        rec = self.recommendations.recommend(
            symbol="BTCUSDT",
            side="long",
            entry_low=67800,
            entry_high=68200,
            stop=66500,
            targets=[70000, 72000, 75000],
            size=1.25,
            duration="swing",
            confidence=0.76,
        )
        alt = self.recommendations.alternative(
            recommendation_id=rec["recommendation_id"],
            name="pullback_entry",
            narrative="Wait for retest of 67.5k if momentum stalls.",
        )

        health = self.portfolio_intel.health(portfolio_id="pf_core", score=81)
        self.portfolio_intel.allocation_review(
            portfolio_id="pf_core",
            advice="Keep BTC overweight; trim speculative beta if volatility expands.",
        )
        self.portfolio_intel.exposure_review(portfolio_id="pf_core", long_pct=68, short_pct=8)
        self.portfolio_intel.diversification(
            portfolio_id="pf_core",
            suggestion="Add uncorrelated cash/stable buffer to 12%.",
        )
        self.portfolio_intel.optimize_advice(
            portfolio_id="pf_core",
            advice="Rebalance SOL down 3% into BTC on strength.",
        )
        self.portfolio_intel.drawdown(portfolio_id="pf_core", current_dd=0.041, limit_dd=0.12)

        overview = self.executive.market_overview(
            summary="Multi-factor bias constructive for majors with selective opportunity ranking.",
            bias="bullish",
        )
        self.executive.top_opportunities(symbols=["BTCUSDT", "ETHUSDT"])
        self.executive.high_risk_assets(symbols=["SOLUSDT", "MEMEUSDT"])
        self.executive.watchlist(symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"], priorities=["BTCUSDT"])
        self.executive.macro_impact(summary="Fed path remains supportive for risk assets.")
        self.executive.whale_summary(summary="Limited distribution into exchanges for BTC; ETH mixed.")
        self.executive.institutional_flow(summary="ETF inflow impulse remains a primary tailwind.")
        actions = self.executive.actions(
            recommendations=[
                "Prioritize BTC long setups with RR >= 2",
                "Cap leverage at 2x in medium risk regime",
                "Monitor SOL unlock calendar for risk events",
            ]
        )

        trace = self.explainability.trace(
            decision_id=decision["decision_id"],
            steps=[
                "aggregate_multi_factor_scores",
                "compute_bias_probabilities",
                "apply_risk_overlay",
                "rank_opportunity",
            ],
        )
        self.explainability.evidence(
            decision_id=decision["decision_id"],
            evidence={
                "technical": "EMA trend + RSI constructive",
                "onchain": "Institutional accumulation detected",
                "news": "ETF inflow narrative supportive",
            },
        )
        expl = self.explainability.summarize(
            decision_id=decision["decision_id"],
            indicators="Trend and momentum aligned on 1h/4h",
            news="ETF inflows accelerate",
            onchain="Whale distribution limited; institutional bid present",
            risk="Medium — loss limits intact",
            confidence_explanation="Six-factor confluence above 0.55 with no critical risk breach",
        )
        report = self.explainability.report(
            decision_id=decision["decision_id"],
            narrative="BTCUSDT ranks as a high-confidence long opportunity with defined invalidation at 66500.",
        )

        alert = self.alerts.raise_alert(
            alert_type="high_confidence",
            symbol="BTCUSDT",
            severity="info",
            message="High-confidence long recommendation published",
        )
        self.alerts.raise_alert(
            alert_type="whale",
            symbol="ETHUSDT",
            severity="warning",
            message="Elevated exchange inflow detected",
        )
        self.alerts.raise_alert(
            alert_type="regime_change",
            severity="info",
            message="Market regime remains trending",
        )
        self.alerts.raise_alert(
            alert_type="portfolio",
            severity="info",
            message="Portfolio health score 81/100",
        )

        for rtype, key in (
            ("decision", decision["decision_id"]),
            ("recommendation", rec["recommendation_id"]),
            ("portfolio", health["health_id"]),
            ("alert", alert["alert_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="ai_trader")
        return {
            "bootstrap": True,
            "decision_id": decision["decision_id"],
            "multi_factor_id": factors["analysis_id"],
            "opportunity_id": opp["opportunity_id"],
            "chat_id": chat["chat_id"],
            "briefing_id": briefing["briefing_id"],
            "recommendation_id": rec["recommendation_id"],
            "alternative_id": alt["alternative_id"],
            "health_id": health["health_id"],
            "overview_id": overview["overview_id"],
            "action_id": actions["action_id"],
            "trace_id": trace["trace_id"],
            "explanation_id": expl["explanation_id"],
            "report_id": report["report_id"],
            "alert_id": alert["alert_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "decision": self.decision.status(),
            "assistant": self.assistant.status(),
            "recommendations": self.recommendations.status(),
            "portfolio_intel": self.portfolio_intel.status(),
            "executive": self.executive.status(),
            "explainability": self.explainability.status(),
            "alerts": self.alerts.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


ai_trader = AITraderSuite()
