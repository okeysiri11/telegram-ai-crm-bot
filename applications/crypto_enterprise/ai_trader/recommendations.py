"""Trade recommendations, portfolio intelligence, and executive support."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TradeRecommendationEngine:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def recommend(
        self,
        *,
        symbol: str,
        side: str,
        entry_low: float,
        entry_high: float,
        stop: float,
        targets: list[float],
        size: float,
        duration: str = "swing",
        confidence: float = 0.7,
    ) -> dict[str, Any]:
        if side not in ("long", "short"):
            raise ValidationError("side must be long|short")
        if not targets:
            raise ValidationError("targets required")
        confidence = float(confidence)
        if confidence < 0 or confidence > 1:
            raise ValidationError("confidence must be 0..1")
        entry_mid = (float(entry_low) + float(entry_high)) / 2
        risk = abs(entry_mid - float(stop))
        reward = abs(float(targets[0]) - entry_mid)
        rr = round(reward / max(risk, 1e-9), 2)
        rid = _id("at_rec")
        return self.store.at_recommendations.save(
            rid,
            {
                "recommendation_id": rid,
                "symbol": symbol.upper(),
                "side": side,
                "entry_zone": [float(entry_low), float(entry_high)],
                "exit_zone": [float(targets[0]), float(targets[-1])],
                "stop": float(stop),
                "targets": [float(t) for t in targets],
                "position_size": float(size),
                "duration": duration,
                "risk_reward": rr,
                "confidence": confidence,
                "at": _now(),
            },
        )

    def alternative(self, *, recommendation_id: str, name: str, narrative: str) -> dict[str, Any]:
        if self.store.at_recommendations.get(recommendation_id) is None:
            raise ValidationError("recommendation_id not found")
        aid = _id("at_alt")
        return self.store.at_alternatives.save(
            aid,
            {
                "alternative_id": aid,
                "recommendation_id": recommendation_id,
                "name": name,
                "narrative": narrative,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "recommendations": self.store.at_recommendations.count(),
            "alternatives": self.store.at_alternatives.count(),
        }


class PortfolioIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def health(self, *, portfolio_id: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        hid = _id("at_ph")
        return self.store.at_port_health.save(
            hid,
            {
                "health_id": hid,
                "portfolio_id": portfolio_id,
                "score": score,
                "status": "healthy" if score >= 70 else "watch" if score >= 40 else "critical",
                "at": _now(),
            },
        )

    def allocation_review(self, *, portfolio_id: str, advice: str) -> dict[str, Any]:
        if not advice:
            raise ValidationError("advice required")
        aid = _id("at_alloc")
        return self.store.at_alloc_review.save(
            aid,
            {"review_id": aid, "portfolio_id": portfolio_id, "advice": advice, "at": _now()},
        )

    def exposure_review(self, *, portfolio_id: str, long_pct: float, short_pct: float) -> dict[str, Any]:
        eid = _id("at_exp")
        return self.store.at_exposure_review.save(
            eid,
            {
                "review_id": eid,
                "portfolio_id": portfolio_id,
                "long_pct": float(long_pct),
                "short_pct": float(short_pct),
                "at": _now(),
            },
        )

    def diversification(self, *, portfolio_id: str, suggestion: str) -> dict[str, Any]:
        did = _id("at_div")
        return self.store.at_diversify.save(
            did,
            {
                "suggestion_id": did,
                "portfolio_id": portfolio_id,
                "suggestion": suggestion,
                "at": _now(),
            },
        )

    def optimize_advice(self, *, portfolio_id: str, advice: str) -> dict[str, Any]:
        oid = _id("at_optadv")
        return self.store.at_opt_advice.save(
            oid,
            {"advice_id": oid, "portfolio_id": portfolio_id, "advice": advice, "at": _now()},
        )

    def drawdown(self, *, portfolio_id: str, current_dd: float, limit_dd: float) -> dict[str, Any]:
        did = _id("at_dd")
        return self.store.at_drawdown.save(
            did,
            {
                "monitor_id": did,
                "portfolio_id": portfolio_id,
                "current_dd": float(current_dd),
                "limit_dd": float(limit_dd),
                "breached": float(current_dd) >= float(limit_dd),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "health": self.store.at_port_health.count(),
            "reviews": self.store.at_alloc_review.count(),
            "drawdown": self.store.at_drawdown.count(),
        }


class ExecutiveDecisionSupport:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def market_overview(self, *, summary: str, bias: str = "neutral") -> dict[str, Any]:
        if bias not in ("bullish", "bearish", "neutral"):
            raise ValidationError("bias must be bullish|bearish|neutral")
        if not summary:
            raise ValidationError("summary required")
        mid = _id("at_mkt")
        return self.store.at_market_overview.save(
            mid,
            {"overview_id": mid, "summary": summary, "bias": bias, "at": _now()},
        )

    def top_opportunities(self, *, symbols: list[str]) -> dict[str, Any]:
        if not symbols:
            raise ValidationError("symbols required")
        tid = _id("at_top")
        return self.store.at_top_ops.save(
            tid,
            {"list_id": tid, "symbols": [s.upper() for s in symbols], "at": _now()},
        )

    def high_risk_assets(self, *, symbols: list[str]) -> dict[str, Any]:
        if not symbols:
            raise ValidationError("symbols required")
        hid = _id("at_hrisk")
        return self.store.at_high_risk.save(
            hid,
            {"list_id": hid, "symbols": [s.upper() for s in symbols], "at": _now()},
        )

    def watchlist(self, *, symbols: list[str], priorities: list[str] | None = None) -> dict[str, Any]:
        if not symbols:
            raise ValidationError("symbols required")
        wid = _id("at_watch")
        return self.store.at_watchlist.save(
            wid,
            {
                "watchlist_id": wid,
                "symbols": [s.upper() for s in symbols],
                "priorities": priorities or [],
                "at": _now(),
            },
        )

    def macro_impact(self, *, summary: str) -> dict[str, Any]:
        mid = _id("at_macro")
        return self.store.at_macro_impact.save(
            mid,
            {"impact_id": mid, "summary": summary, "at": _now()},
        )

    def whale_summary(self, *, summary: str) -> dict[str, Any]:
        wid = _id("at_whale")
        return self.store.at_whale_summary.save(
            wid,
            {"summary_id": wid, "summary": summary, "at": _now()},
        )

    def institutional_flow(self, *, summary: str) -> dict[str, Any]:
        iid = _id("at_inst")
        return self.store.at_inst_flow.save(
            iid,
            {"summary_id": iid, "summary": summary, "at": _now()},
        )

    def actions(self, *, recommendations: list[str]) -> dict[str, Any]:
        if not recommendations:
            raise ValidationError("recommendations required")
        aid = _id("at_act")
        return self.store.at_exec_actions.save(
            aid,
            {"action_id": aid, "recommendations": recommendations, "at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {
            "overviews": self.store.at_market_overview.count(),
            "watchlists": self.store.at_watchlist.count(),
            "actions": self.store.at_exec_actions.count(),
        }
