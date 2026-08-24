"""Technical analysis from OHLC bars — no fabrication when empty."""

from __future__ import annotations

from typing import Any


def _closes(bars: list[dict[str, Any]]) -> list[float]:
    return [float(b.get("c") or b.get("close") or 0) for b in bars if (b.get("c") or b.get("close")) is not None]


def _ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    k = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for v in values[period:]:
        ema = v * k + ema * (1 - k)
    return ema


def _rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _macd(closes: list[float]) -> dict[str, float | None]:
    if len(closes) < 26:
        return {"macd": None, "signal": None, "histogram": None}
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    if ema12 is None or ema26 is None:
        return {"macd": None, "signal": None, "histogram": None}
    # Build MACD series for signal EMA
    k12, k26 = 2 / 13, 2 / 27
    e12 = sum(closes[:12]) / 12
    e26 = sum(closes[:26]) / 26
    macd_series: list[float] = []
    for i, v in enumerate(closes):
        if i >= 12:
            e12 = v * k12 + e12 * (1 - k12)
        if i >= 26:
            e26 = v * k26 + e26 * (1 - k26)
        if i >= 25:
            macd_series.append(e12 - e26)
    if len(macd_series) < 9:
        macd = ema12 - ema26
        return {"macd": round(macd, 6), "signal": None, "histogram": None}
    signal = _ema(macd_series, 9)
    macd = macd_series[-1]
    hist = None if signal is None else macd - signal
    return {
        "macd": round(macd, 6),
        "signal": round(signal, 6) if signal is not None else None,
        "histogram": round(hist, 6) if hist is not None else None,
    }


def _atr(bars: list[dict[str, Any]], period: int = 14) -> float | None:
    if len(bars) < period + 1:
        return None
    trs: list[float] = []
    prev_c = float(bars[0].get("c") or bars[0].get("close") or 0)
    for b in bars[1:]:
        h = float(b.get("h") or b.get("high") or prev_c)
        l = float(b.get("l") or b.get("low") or prev_c)
        c = float(b.get("c") or b.get("close") or prev_c)
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
        prev_c = c
    if len(trs) < period:
        return None
    return sum(trs[-period:]) / period


def _bollinger(closes: list[float], period: int = 20) -> dict[str, float | None]:
    if len(closes) < period:
        return {"mid": None, "upper": None, "lower": None}
    window = closes[-period:]
    mid = sum(window) / period
    var = sum((x - mid) ** 2 for x in window) / period
    std = var ** 0.5
    return {"mid": round(mid, 6), "upper": round(mid + 2 * std, 6), "lower": round(mid - 2 * std, 6)}


def compute_indicators(bars: list[dict[str, Any]]) -> dict[str, Any]:
    """bars: [{c|close, h|high, l|low, ...}]. No fabrication if empty."""
    empty = {
        "status": "insufficient_data",
        "message": "Недостаточно данных для индикаторов",
        "trend": None,
        "ema_fast": None,
        "ema_slow": None,
        "sma_fast": None,
        "sma_slow": None,
        "rsi": None,
        "macd": None,
        "macd_signal": None,
        "macd_hist": None,
        "atr": None,
        "bollinger": {"mid": None, "upper": None, "lower": None},
        "support": None,
        "resistance": None,
        "bias": "NEUTRAL",
    }
    if not bars or len(bars) < 2:
        return empty
    closes = _closes(bars)
    highs = [float(b.get("h") or b.get("high") or c) for b, c in zip(bars, closes)]
    lows = [float(b.get("l") or b.get("low") or c) for b, c in zip(bars, closes)]
    if len(closes) < 5:
        return {
            **empty,
            "message": "Мало баров для индикаторов",
            "support": min(lows) if lows else None,
            "resistance": max(highs) if highs else None,
        }
    n_fast, n_slow = 5, min(20, len(closes))
    sma_fast = sum(closes[-n_fast:]) / n_fast
    sma_slow = sum(closes[-n_slow:]) / n_slow
    ema_fast = _ema(closes, 12)
    ema_slow = _ema(closes, 26)
    rsi = _rsi(closes)
    macd = _macd(closes)
    atr = _atr(bars)
    bb = _bollinger(closes)
    if ema_fast is not None and ema_slow is not None:
        trend = "up" if ema_fast > ema_slow else "down" if ema_fast < ema_slow else "flat"
    else:
        trend = "up" if sma_fast > sma_slow else "down" if sma_fast < sma_slow else "flat"
    bias = (
        "WATCH_BUY"
        if trend == "up" and (rsi is None or rsi < 70)
        else "WATCH_SELL"
        if trend == "down" and (rsi is None or rsi > 30)
        else "NEUTRAL"
    )
    return {
        "status": "ok",
        "message": "Индикаторы по предоставленным барам",
        "trend": trend,
        "ema_fast": round(ema_fast, 6) if ema_fast is not None else None,
        "ema_slow": round(ema_slow, 6) if ema_slow is not None else None,
        "sma_fast": round(sma_fast, 6),
        "sma_slow": round(sma_slow, 6),
        "rsi": round(rsi, 2) if rsi is not None else None,
        "macd": macd.get("macd"),
        "macd_signal": macd.get("signal"),
        "macd_hist": macd.get("histogram"),
        "atr": round(atr, 6) if atr is not None else None,
        "bollinger": bb,
        "support": round(min(lows[-n_slow:]), 6),
        "resistance": round(max(highs[-n_slow:]), 6),
        "bias": bias,
    }
