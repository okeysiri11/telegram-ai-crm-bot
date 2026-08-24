"""Specialist configuration schemas — stored in prefs + optional DB payload."""

from __future__ import annotations

from typing import Any

SOUND_PROFILES = [
    {"id": "standard", "label_ru": "Стандартный"},
    {"id": "eurusd", "label_ru": "EUR/USD"},
    {"id": "dxy", "label_ru": "DXY"},
    {"id": "analysis", "label_ru": "Анализ"},
    {"id": "important", "label_ru": "Важное событие"},
    {"id": "silent", "label_ru": "Без звука"},
]

SIGNAL_KINDS = [
    {"id": "price_alert", "label_ru": "Price alert"},
    {"id": "analysis_result", "label_ru": "Analysis result"},
    {"id": "agent_event", "label_ru": "Agent event"},
    {"id": "scheduled_event", "label_ru": "Scheduled event"},
    {"id": "macro_alert", "label_ru": "Macro alert"},
]


def default_specialist_settings(agent_id: str) -> dict[str, Any]:
    base = {
        "enabled": True,
        "instruments": ["EUR/USD", "DXY"],
        "timeframes": ["1H"],
        "weight": 1.0,
        "minimum_confidence": 0.3,
        "include_in_chief_consensus": True,
        "allow_signal_generation": True,
        "alert_level": "medium",
    }
    if agent_id == "technical":
        return {
            **base,
            "indicators": {
                "ema": True,
                "sma": True,
                "rsi": True,
                "macd": True,
                "bollinger": True,
                "atr": True,
                "support_resistance": True,
            },
            "timeframes": ["15m", "1H", "4H", "1D"],
        }
    if agent_id == "dxy":
        return {
            **base,
            "instruments": ["DXY"],
            "dxy_enabled": True,
            "timeframe": "1H",
            "sensitivity": "medium",
            "divergence_monitoring": True,
            "inverse_eurusd_relation": True,
            "correlation_threshold": 0.5,
        }
    if agent_id == "macro":
        return {
            **base,
            "impact": ["medium", "high"],
            "currencies": ["EUR", "USD"],
            "events": ["ECB", "FED", "CPI", "NFP", "GDP", "PCE", "unemployment", "rates", "PMI"],
        }
    if agent_id == "news":
        return {
            **base,
            "sources": {"ecb": True, "fed": True, "reuters_compatible": True, "official_feeds": True, "configured_rss": True},
            "freshness_hours": 24,
            "duplicate_filtering": True,
            "importance": "medium",
            "sentiment": True,
        }
    if agent_id == "risk":
        return {
            **base,
            "max_risk_per_trade_pct": 1.0,
            "max_daily_loss": 500.0,
            "max_open_positions": 5,
            "minimum_rr": 1.5,
            "stop_after_n_losses": 3,
            "max_drawdown_threshold": 5.0,
            "strict": False,
        }
    if agent_id == "chief":
        return {**base, "weight": 1.0, "show_vote_table": True}
    return base
