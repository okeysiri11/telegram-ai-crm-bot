"""AI technical intelligence, dashboards, and knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

DASHBOARD_TYPES = ["trading", "indicator", "pattern", "ai_analysis"]
REGISTRY_TYPES = ["technical", "indicator", "pattern", "tradingview"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AITechnicalIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def trend_strength(self, *, symbol: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 1:
            raise ValidationError("score must be 0..1")
        tid = _id("ta_atrend")
        return self.store.ta_ai_trend.save(
            tid,
            {
                "analysis_id": tid,
                "symbol": symbol.upper(),
                "score": score,
                "label": "strong" if score >= 0.7 else "moderate" if score >= 0.4 else "weak",
                "at": _now(),
            },
        )

    def momentum(self, *, symbol: str, rsi: float = 55.0) -> dict[str, Any]:
        mid = _id("ta_amom")
        return self.store.ta_ai_momentum.save(
            mid,
            {
                "analysis_id": mid,
                "symbol": symbol.upper(),
                "rsi": float(rsi),
                "state": "bullish" if rsi >= 55 else "bearish",
                "at": _now(),
            },
        )

    def volatility(self, *, symbol: str, atr_pct: float) -> dict[str, Any]:
        vid = _id("ta_avol")
        return self.store.ta_ai_volatility.save(
            vid,
            {
                "analysis_id": vid,
                "symbol": symbol.upper(),
                "atr_pct": float(atr_pct),
                "regime": "high" if atr_pct >= 3 else "normal",
                "at": _now(),
            },
        )

    def confluence(self, *, symbol: str, indicators: list[str]) -> dict[str, Any]:
        if not indicators:
            raise ValidationError("indicators required")
        cid = _id("ta_aconf")
        return self.store.ta_ai_confluence.save(
            cid,
            {
                "analysis_id": cid,
                "symbol": symbol.upper(),
                "indicators": indicators,
                "aligned": len(indicators),
                "score": min(0.95, 0.55 + 0.05 * len(indicators)),
                "at": _now(),
            },
        )

    def multi_timeframe_confirm(self, *, symbol: str, timeframes: list[str]) -> dict[str, Any]:
        if not timeframes:
            raise ValidationError("timeframes required")
        mid = _id("ta_amtf")
        return self.store.ta_ai_mtf.save(
            mid,
            {
                "confirmation_id": mid,
                "symbol": symbol.upper(),
                "timeframes": timeframes,
                "confirmed": True,
                "at": _now(),
            },
        )

    def signal_confidence(self, *, symbol: str, side: str, confidence: float) -> dict[str, Any]:
        if side not in ("long", "short", "neutral"):
            raise ValidationError("side must be long|short|neutral")
        confidence = float(confidence)
        if confidence < 0 or confidence > 1:
            raise ValidationError("confidence must be 0..1")
        sid = _id("ta_asig")
        return self.store.ta_ai_signals.save(
            sid,
            {
                "signal_id": sid,
                "symbol": symbol.upper(),
                "side": side,
                "confidence": confidence,
                "at": _now(),
            },
        )

    def trade_setup(self, *, symbol: str, entry: float, stop: float, target: float) -> dict[str, Any]:
        tid = _id("ta_asetup")
        return self.store.ta_ai_setups.save(
            tid,
            {
                "setup_id": tid,
                "symbol": symbol.upper(),
                "entry": float(entry),
                "stop": float(stop),
                "target": float(target),
                "rr": round(abs(float(target) - float(entry)) / max(abs(float(entry) - float(stop)), 1e-9), 2),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "trend": self.store.ta_ai_trend.count(),
            "signals": self.store.ta_ai_signals.count(),
            "setups": self.store.ta_ai_setups.count(),
        }


class TechnicalDashboard:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "trading") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "trading": {
                "charts": self.store.ta_charts.count(),
                "alerts": self.store.ta_alerts.count(),
            },
            "indicator": {
                "indicators": self.store.ta_indicators.count(),
            },
            "pattern": {
                "patterns": self.store.ta_patterns.count(),
                "structures": self.store.ta_structures.count(),
            },
            "ai_analysis": {
                "signals": self.store.ta_ai_signals.count(),
                "setups": self.store.ta_ai_setups.count(),
            },
        }[dashboard_type]
        did = _id("ta_dash")
        return self.store.ta_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ta_dashboards.count(), "types": self.types}


class TechnicalKnowledge:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("ta_reg")
        return self.store.ta_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"ta:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.ta_registries.count(), "types": self.types}
