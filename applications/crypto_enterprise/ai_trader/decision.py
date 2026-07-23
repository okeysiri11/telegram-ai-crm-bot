"""AI decision center and trading assistant."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

BIAS = ["bullish", "bearish", "neutral"]
RISK_BANDS = ["low", "medium", "high", "extreme"]
CHAT_TOPICS = [
    "market",
    "asset_compare",
    "strategy_review",
    "trade_review",
    "portfolio_review",
    "daily_briefing",
    "executive_summary",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIDecisionCenter:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def decide(
        self,
        *,
        symbol: str,
        factors: list[str] | None = None,
        bullish: float = 0.5,
        bearish: float = 0.3,
        confidence: float = 0.7,
        risk: str = "medium",
    ) -> dict[str, Any]:
        bullish = float(bullish)
        bearish = float(bearish)
        confidence = float(confidence)
        if bullish < 0 or bullish > 1 or bearish < 0 or bearish > 1:
            raise ValidationError("probabilities must be 0..1")
        if confidence < 0 or confidence > 1:
            raise ValidationError("confidence must be 0..1")
        if risk not in RISK_BANDS:
            raise ValidationError(f"risk must be one of {RISK_BANDS}")
        neutral = round(max(0.0, 1.0 - bullish - bearish), 4)
        bias = "bullish" if bullish >= bearish and bullish >= neutral else "bearish" if bearish >= neutral else "neutral"
        did = _id("at_dec")
        return self.store.at_decisions.save(
            did,
            {
                "decision_id": did,
                "symbol": symbol.upper(),
                "factors": factors or ["technical", "derivatives", "onchain", "news", "sentiment", "risk"],
                "bullish": bullish,
                "bearish": bearish,
                "neutral": neutral,
                "bias": bias,
                "confidence": confidence,
                "risk": risk,
                "at": _now(),
            },
        )

    def multi_factor(self, *, symbol: str, scores: dict[str, float]) -> dict[str, Any]:
        if not scores:
            raise ValidationError("scores required")
        mid = _id("at_mf")
        avg = sum(scores.values()) / max(len(scores), 1)
        return self.store.at_multi_factor.save(
            mid,
            {
                "analysis_id": mid,
                "symbol": symbol.upper(),
                "scores": scores,
                "aggregate": round(avg, 4),
                "at": _now(),
            },
        )

    def scenario(self, *, symbol: str, name: str, outcome: str, probability: float) -> dict[str, Any]:
        probability = float(probability)
        if probability < 0 or probability > 1:
            raise ValidationError("probability must be 0..1")
        sid = _id("at_scen")
        return self.store.at_scenarios.save(
            sid,
            {
                "scenario_id": sid,
                "symbol": symbol.upper(),
                "name": name,
                "outcome": outcome,
                "probability": probability,
                "at": _now(),
            },
        )

    def rank_opportunity(self, *, symbol: str, score: float, thesis: str = "") -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        rid = _id("at_opp")
        return self.store.at_opportunities.save(
            rid,
            {
                "opportunity_id": rid,
                "symbol": symbol.upper(),
                "score": score,
                "thesis": thesis,
                "rank_band": "high" if score >= 75 else "medium" if score >= 50 else "low",
                "at": _now(),
            },
        )

    def classify_risk(self, *, symbol: str, risk: str, rationale: str = "") -> dict[str, Any]:
        if risk not in RISK_BANDS:
            raise ValidationError(f"risk must be one of {RISK_BANDS}")
        cid = _id("at_risk")
        return self.store.at_risk_class.save(
            cid,
            {
                "classification_id": cid,
                "symbol": symbol.upper(),
                "risk": risk,
                "rationale": rationale,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "decisions": self.store.at_decisions.count(),
            "scenarios": self.store.at_scenarios.count(),
            "opportunities": self.store.at_opportunities.count(),
        }


class AITradingAssistant:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def chat(self, *, topic: str, question: str, answer: str = "") -> dict[str, Any]:
        if topic not in CHAT_TOPICS:
            raise ValidationError(f"topic must be one of {CHAT_TOPICS}")
        if not question:
            raise ValidationError("question required")
        default_answers = {
            "market": "Multi-factor bias is constructive with medium confidence.",
            "asset_compare": "Relative strength favors the higher-ranked opportunity.",
            "strategy_review": "Strategy confluence remains aligned with regime.",
            "trade_review": "Risk/reward and stop placement appear disciplined.",
            "portfolio_review": "Exposure is within policy; diversification is adequate.",
            "daily_briefing": "Risk-on tone with selective opportunities in majors.",
            "executive_summary": "Maintain core exposure; prioritize high-confidence setups.",
        }
        cid = _id("at_chat")
        return self.store.at_chat.save(
            cid,
            {
                "chat_id": cid,
                "topic": topic,
                "question": question,
                "answer": answer or default_answers.get(topic, "Acknowledged."),
                "at": _now(),
            },
        )

    def compare_assets(self, *, symbols: list[str], winner: str = "") -> dict[str, Any]:
        if len(symbols) < 2:
            raise ValidationError("at least two symbols required")
        cid = _id("at_cmp")
        return self.store.at_comparisons.save(
            cid,
            {
                "comparison_id": cid,
                "symbols": [s.upper() for s in symbols],
                "winner": (winner or symbols[0]).upper(),
                "at": _now(),
            },
        )

    def briefing(self, *, briefing_type: str, summary: str) -> dict[str, Any]:
        if briefing_type not in ("daily", "executive"):
            raise ValidationError("briefing_type must be daily|executive")
        if not summary:
            raise ValidationError("summary required")
        bid = _id("at_brief")
        return self.store.at_briefings.save(
            bid,
            {
                "briefing_id": bid,
                "briefing_type": briefing_type,
                "summary": summary,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "chat": self.store.at_chat.count(),
            "comparisons": self.store.at_comparisons.count(),
            "briefings": self.store.at_briefings.count(),
        }
