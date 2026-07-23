"""Technical indicators, chart analysis, and pattern recognition."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

INDICATORS = [
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
]

STRUCTURES = [
    "support",
    "resistance",
    "trendline",
    "channel",
    "triangle",
    "flag",
    "wedge",
    "breakout",
]

PATTERNS = [
    "head_shoulders",
    "double_top",
    "double_bottom",
    "cup_handle",
    "ascending_triangle",
    "descending_triangle",
    "bull_flag",
    "bear_flag",
    "candlestick",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TechnicalIndicators:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.supported = list(INDICATORS)

    def compute(
        self,
        *,
        indicator: str,
        symbol: str,
        timeframe: str = "1h",
        period: int = 14,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if indicator not in INDICATORS:
            raise ValidationError(f"indicator must be one of {INDICATORS}")
        if not symbol:
            raise ValidationError("symbol required")
        values = self._synthetic(indicator, period)
        iid = _id("ta_ind")
        return self.store.ta_indicators.save(
            iid,
            {
                "indicator_id": iid,
                "indicator": indicator,
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "period": int(period),
                "params": params or {},
                "values": values,
                "at": _now(),
            },
        )

    def _synthetic(self, indicator: str, period: int) -> dict[str, Any]:
        base = {
            "sma": {"value": 68050.0},
            "ema": {"value": 68120.0},
            "macd": {"macd": 120.5, "signal": 95.2, "histogram": 25.3},
            "rsi": {"value": 58.4},
            "stoch_rsi": {"k": 62.1, "d": 55.0},
            "bollinger": {"upper": 69500.0, "mid": 68000.0, "lower": 66500.0},
            "vwap": {"value": 67980.0},
            "atr": {"value": 850.0},
            "adx": {"value": 27.5},
            "ichimoku": {"tenkan": 67800.0, "kijun": 67200.0, "span_a": 67500.0, "span_b": 66800.0},
            "parabolic_sar": {"value": 67000.0, "trend": "up"},
            "supertrend": {"value": 67250.0, "trend": "bullish"},
        }[indicator]
        base["period"] = period
        return base

    def status(self) -> dict[str, Any]:
        return {"indicators": self.store.ta_indicators.count(), "supported": self.supported}


class ChartAnalysis:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.structures = list(STRUCTURES)

    def detect(self, *, structure: str, symbol: str, price: float = 0.0) -> dict[str, Any]:
        if structure not in STRUCTURES:
            raise ValidationError(f"structure must be one of {STRUCTURES}")
        if not symbol:
            raise ValidationError("symbol required")
        sid = _id("ta_str")
        level = float(price) if price else {
            "support": 66500.0,
            "resistance": 69500.0,
            "trendline": 67800.0,
            "channel": 68200.0,
            "triangle": 68500.0,
            "flag": 68100.0,
            "wedge": 68300.0,
            "breakout": 69600.0,
        }[structure]
        return self.store.ta_structures.save(
            sid,
            {
                "structure_id": sid,
                "structure": structure,
                "symbol": symbol.upper(),
                "level": level,
                "confidence": 0.82,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"structures": self.store.ta_structures.count(), "types": self.structures}


class PatternRecognition:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.patterns = list(PATTERNS)

    def recognize(
        self,
        *,
        pattern: str,
        symbol: str,
        timeframe: str = "1h",
        candle_pattern: str = "",
    ) -> dict[str, Any]:
        if pattern not in PATTERNS:
            raise ValidationError(f"pattern must be one of {PATTERNS}")
        if not symbol:
            raise ValidationError("symbol required")
        pid = _id("ta_pat")
        bias = {
            "head_shoulders": "bearish",
            "double_top": "bearish",
            "double_bottom": "bullish",
            "cup_handle": "bullish",
            "ascending_triangle": "bullish",
            "descending_triangle": "bearish",
            "bull_flag": "bullish",
            "bear_flag": "bearish",
            "candlestick": "neutral",
        }[pattern]
        return self.store.ta_patterns.save(
            pid,
            {
                "pattern_id": pid,
                "pattern": pattern,
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "candle_pattern": candle_pattern,
                "bias": bias,
                "confidence": 0.79,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"patterns": self.store.ta_patterns.count(), "types": self.patterns}
