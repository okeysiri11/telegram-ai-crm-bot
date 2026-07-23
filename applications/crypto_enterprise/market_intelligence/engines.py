"""AI correlation/decision engines, dashboards, and knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

CORRELATION_TYPES = [
    "news_price",
    "sentiment_volume",
    "macro_market",
    "whale_price",
    "funding_trend",
    "oi_momentum",
]
DASHBOARD_TYPES = ["news", "sentiment", "macro", "correlation", "ai_market"]
REGISTRY_TYPES = ["intelligence", "news", "sentiment", "macro", "correlation"]
OUTLOOK_HORIZONS = ["short", "medium", "long"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AICorrelationEngine:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def correlate(
        self,
        *,
        correlation_type: str,
        symbol: str,
        coefficient: float,
        window: str = "7d",
    ) -> dict[str, Any]:
        if correlation_type not in CORRELATION_TYPES:
            raise ValidationError(f"correlation_type must be one of {CORRELATION_TYPES}")
        coefficient = float(coefficient)
        if coefficient < -1 or coefficient > 1:
            raise ValidationError("coefficient must be -1..1")
        cid = _id("mi_corr")
        return self.store.mi_correlations.save(
            cid,
            {
                "correlation_id": cid,
                "correlation_type": correlation_type,
                "symbol": symbol.upper(),
                "coefficient": coefficient,
                "window": window,
                "strength": "strong" if abs(coefficient) >= 0.6 else "moderate" if abs(coefficient) >= 0.3 else "weak",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"correlations": self.store.mi_correlations.count(), "types": list(CORRELATION_TYPES)}


class AIDecisionEngine:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def market_summary(self, *, symbol: str, summary: str) -> dict[str, Any]:
        if not summary:
            raise ValidationError("summary required")
        sid = _id("mi_sum")
        return self.store.mi_summaries.save(
            sid,
            {"summary_id": sid, "symbol": symbol.upper(), "summary": summary, "at": _now()},
        )

    def risk_level(self, *, symbol: str, level: str, score: float) -> dict[str, Any]:
        if level not in ("low", "medium", "high", "extreme"):
            raise ValidationError("level must be low|medium|high|extreme")
        rid = _id("mi_risk")
        return self.store.mi_risk.save(
            rid,
            {
                "risk_id": rid,
                "symbol": symbol.upper(),
                "level": level,
                "score": float(score),
                "at": _now(),
            },
        )

    def opportunity(self, *, symbol: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        oid = _id("mi_opp")
        return self.store.mi_opportunity.save(
            oid,
            {"opportunity_id": oid, "symbol": symbol.upper(), "score": score, "at": _now()},
        )

    def probabilities(self, *, symbol: str, bullish: float, bearish: float) -> dict[str, Any]:
        bullish = float(bullish)
        bearish = float(bearish)
        if bullish < 0 or bullish > 1 or bearish < 0 or bearish > 1:
            raise ValidationError("probabilities must be 0..1")
        pid = _id("mi_prob")
        return self.store.mi_probabilities.save(
            pid,
            {
                "probability_id": pid,
                "symbol": symbol.upper(),
                "bullish": bullish,
                "bearish": bearish,
                "neutral": round(max(0.0, 1.0 - bullish - bearish), 4),
                "at": _now(),
            },
        )

    def volatility_forecast(self, *, symbol: str, forecast_pct: float, horizon: str = "7d") -> dict[str, Any]:
        vid = _id("mi_volf")
        return self.store.mi_vol_forecast.save(
            vid,
            {
                "forecast_id": vid,
                "symbol": symbol.upper(),
                "forecast_pct": float(forecast_pct),
                "horizon": horizon,
                "at": _now(),
            },
        )

    def outlook(self, *, symbol: str, horizon: str, bias: str, narrative: str) -> dict[str, Any]:
        if horizon not in OUTLOOK_HORIZONS:
            raise ValidationError(f"horizon must be one of {OUTLOOK_HORIZONS}")
        if bias not in ("bullish", "bearish", "neutral"):
            raise ValidationError("bias must be bullish|bearish|neutral")
        oid = _id("mi_out")
        return self.store.mi_outlooks.save(
            oid,
            {
                "outlook_id": oid,
                "symbol": symbol.upper(),
                "horizon": horizon,
                "bias": bias,
                "narrative": narrative,
                "at": _now(),
            },
        )

    def explain(self, *, symbol: str, explanation: str) -> dict[str, Any]:
        if not explanation:
            raise ValidationError("explanation required")
        eid = _id("mi_expl")
        return self.store.mi_explanations.save(
            eid,
            {
                "explanation_id": eid,
                "symbol": symbol.upper(),
                "explanation": explanation,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "summaries": self.store.mi_summaries.count(),
            "risk": self.store.mi_risk.count(),
            "opportunity": self.store.mi_opportunity.count(),
            "outlooks": self.store.mi_outlooks.count(),
        }


class IntelligenceDashboard:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "news") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "news": {
                "feed": self.store.mi_news_feed.count(),
                "breaking": self.store.mi_breaking.count(),
            },
            "sentiment": {
                "index": self.store.mi_sentiment_index.count(),
                "fear_greed": self.store.mi_fear_greed.count(),
            },
            "macro": {
                "events": self.store.mi_macro_events.count(),
            },
            "correlation": {
                "correlations": self.store.mi_correlations.count(),
            },
            "ai_market": {
                "summaries": self.store.mi_summaries.count(),
                "outlooks": self.store.mi_outlooks.count(),
                "opportunity": self.store.mi_opportunity.count(),
            },
        }[dashboard_type]
        did = _id("mi_dash")
        return self.store.mi_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.mi_dashboards.count(), "types": self.types}


class IntelligenceKnowledge:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("mi_reg")
        return self.store.mi_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"mi:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.mi_registries.count(), "types": self.types}
