"""Yahoo Finance chart feed for EURUSD bars and DXY — no fabricated prices."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import aiohttp

from services.fx_market_intel.providers import MarketDataProvider, NbuCrossEurUsdProvider, _now
from services.fx_market_intel.symbols import normalize_symbol

YAHOO_SYMBOLS = {
    "EUR/USD": "EURUSD=X",
    "DXY": "DX-Y.NYB",
}

_TF_MAP = {
    "1m": ("1m", "1d"),
    "1M": ("1m", "1d"),
    "5m": ("5m", "5d"),
    "5M": ("5m", "5d"),
    "15m": ("15m", "5d"),
    "15M": ("15m", "5d"),
    "1h": ("60m", "30d"),
    "1H": ("60m", "30d"),
    "4h": ("60m", "30d"),
    "4H": ("60m", "30d"),
    "1d": ("1d", "6mo"),
    "1D": ("1d", "6mo"),
    "1w": ("1wk", "2y"),
    "1W": ("1wk", "2y"),
}

_HEADERS = {"User-Agent": "ADOS-FX-Intel/50.7"}


class YahooHttpError(RuntimeError):
    def __init__(self, status: int, retry_after: str | None = None) -> None:
        super().__init__(f"Yahoo HTTP {status}")
        self.status = int(status)
        self.retry_after = retry_after


# DXY uses native Yahoo intervals. Never map 1m/5m/15m onto 60m.
_TF_MAP_DXY = {
    "1m": ("1m", "1d"),
    "1M": ("1m", "1d"),
    "5m": ("5m", "5d"),
    "5M": ("5m", "5d"),
    "15m": ("15m", "5d"),
    "15M": ("15m", "5d"),
    "1h": ("60m", "30d"),
    "1H": ("60m", "30d"),
    "4h": ("60m", "30d"),
    "4H": ("60m", "30d"),
    "1d": ("1d", "6mo"),
    "1D": ("1d", "6mo"),
    "1w": ("1wk", "2y"),
    "1W": ("1wk", "2y"),
}

SUPPORTED_TIMEFRAMES = ("1m", "5m", "15m", "1H", "4H", "1D", "1W")
DXY_SUPPORTED_TIMEFRAMES = ("1m", "5m", "15m", "1H", "4H", "1D", "1W")

_CANON_TF = {
    "1m": "1m",
    "1M": "1m",
    "5m": "5m",
    "5M": "5m",
    "15m": "15m",
    "15M": "15m",
    "1h": "1H",
    "1H": "1H",
    "4h": "4H",
    "4H": "4H",
    "1d": "1D",
    "1D": "1D",
    "1w": "1W",
    "1W": "1W",
}


def format_yahoo_mid(instrument: str, price: float) -> str:
    """Keep source precision for live candles: EURUSD 5 dp, DXY 3 dp. Never fabricate ticks."""
    value = float(price)
    if instrument == "EUR/USD":
        return f"{value:.5f}"
    return f"{value:.3f}"


def _maps_for(instrument: str | None) -> tuple[dict[str, tuple[str, str]], tuple[str, ...]]:
    if instrument == "DXY":
        return _TF_MAP_DXY, DXY_SUPPORTED_TIMEFRAMES
    return _TF_MAP, SUPPORTED_TIMEFRAMES


def yahoo_interval_range(instrument: str, timeframe: str) -> tuple[str, str]:
    tf_map, _supported = _maps_for(instrument)
    tf = normalize_timeframe(timeframe, instrument=instrument)
    return tf_map.get(tf, ("60m", "10d"))


def normalize_timeframe(timeframe: str, instrument: str | None = None) -> str:
    raw = (timeframe or "1H").strip()
    maps, _supported = _maps_for(instrument)
    key = raw if raw in maps else raw.upper() if raw.upper() in maps else raw.lower()
    if key not in maps:
        return "1H"
    return _CANON_TF.get(key, "1H")


async def fetch_yahoo_chart(symbol_yahoo: str, *, interval: str, range_: str) -> dict[str, Any]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol_yahoo}"
    params = {"interval": interval, "range": range_}
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                raise YahooHttpError(resp.status, resp.headers.get("Retry-After"))
            data = await resp.json(content_type=None)
    err = (data.get("chart") or {}).get("error")
    if err:
        raise RuntimeError(str(err))
    results = (data.get("chart") or {}).get("result") or []
    if not results:
        raise RuntimeError("Yahoo empty result")
    return results[0]


def _finite(value: Any) -> float | None:
    if value is None:
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(n):
        return None
    return n


def price_in_instrument_band(instrument: str | None, price: float) -> bool:
    """Reject unit/format corruption only (EURUSD 11610, DXY 0, etc.)."""
    if not math.isfinite(price) or price <= 0:
        return False
    sym = instrument or ""
    if sym == "DXY":
        return 20.0 <= price <= 200.0
    return 0.2 <= price <= 5.0


def valid_ohlc(o: float, h: float, l: float, c: float, instrument: str | None = None) -> bool:
    if not all(math.isfinite(x) for x in (o, h, l, c)):
        return False
    if min(o, h, l, c) <= 0:
        return False
    if h < l:
        return False
    if h < max(o, c) or l > min(o, c):
        return False
    if h / l > 20:
        return False
    if instrument and not all(price_in_instrument_band(instrument, x) for x in (o, h, l, c)):
        return False
    return True


def aggregate_ohlc_4h(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate real 1h (or finer) OHLC into 4h buckets. No synthetic prices."""
    buckets: dict[str, dict[str, Any]] = {}
    for b in bars:
        dt = datetime.fromisoformat(b["t"])
        key_h = (dt.hour // 4) * 4
        key = dt.replace(hour=key_h, minute=0, second=0, microsecond=0).isoformat()
        cur = buckets.get(key)
        if not cur:
            buckets[key] = {**b, "t": key, "timeframe": "4H"}
        else:
            cur["h"] = max(cur["h"], b["h"])
            cur["l"] = min(cur["l"], b["l"])
            cur["c"] = b["c"]
            if b.get("v") is not None:
                cur["v"] = (cur.get("v") or 0) + b["v"]
    return [buckets[k] for k in sorted(buckets)]


def _dedupe_sorted_bars(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(bars, key=lambda b: str(b.get("t") or ""))
    out: list[dict[str, Any]] = []
    for b in ordered:
        if out and out[-1].get("t") == b.get("t"):
            out[-1] = b
        else:
            out.append(b)
    return out


def normalize_yahoo_bars(
    result: dict[str, Any],
    *,
    timeframe: str,
    instrument: str | None = None,
) -> list[dict[str, Any]]:
    ts = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    bars: list[dict[str, Any]] = []
    for i, t in enumerate(ts):
        c = _finite(closes[i] if i < len(closes) else None)
        if c is None:
            continue
        o = _finite(opens[i] if i < len(opens) else None)
        h = _finite(highs[i] if i < len(highs) else None)
        l = _finite(lows[i] if i < len(lows) else None)
        v = _finite(volumes[i] if i < len(volumes) else None)
        if o is None and h is None and l is None:
            # Quote-only row. Do not fabricate o=h=l=c dashes.
            continue
        open_ = o if o is not None else c
        high_ = h if h is not None else max(open_, c)
        low_ = l if l is not None else min(open_, c)
        high_ = max(high_, open_, c)
        low_ = min(low_, open_, c)
        if not valid_ohlc(open_, high_, low_, c, instrument):
            continue
        unix = int(t)
        if unix > 1_000_000_000_000:
            unix = unix // 1000
        bars.append(
            {
                "t": datetime.fromtimestamp(unix, tz=timezone.utc).isoformat(),
                "time": unix,
                "o": open_,
                "h": high_,
                "l": low_,
                "c": c,
                "open": open_,
                "high": high_,
                "low": low_,
                "close": c,
                "v": v,
                "timeframe": timeframe,
                "provider": "yahoo",
            }
        )
    bars = _dedupe_sorted_bars(bars)
    if timeframe.upper() == "4H" and bars:
        bars = aggregate_ohlc_4h(bars)
        for b in bars:
            unix = int(datetime.fromisoformat(str(b["t"]).replace("Z", "+00:00")).timestamp())
            b["time"] = unix
            b["open"] = b["o"]
            b["high"] = b["h"]
            b["low"] = b["l"]
            b["close"] = b["c"]
            b.setdefault("provider", "yahoo")
    return bars


class YahooQuoteProvider(MarketDataProvider):
    """Live quote from Yahoo chart meta.regularMarketPrice."""

    def __init__(self, *, instrument: str, label: str | None = None, quote_interval: str = "1d") -> None:
        self.instrument = normalize_symbol(instrument)
        yahoo = YAHOO_SYMBOLS.get(self.instrument)
        if not yahoo:
            raise ValueError(f"Unsupported Yahoo instrument: {instrument}")
        self.yahoo_symbol = yahoo
        self.quote_interval = quote_interval or "1d"
        self.id = f"yahoo_{self.instrument.lower().replace('/', '')}"
        self.label = label or f"Yahoo Finance ({self.yahoo_symbol})"

    async def status(self) -> dict[str, Any]:
        q = await self.get_quote(self.instrument)
        return {
            "provider_id": self.id,
            "label": self.label,
            "status": q.get("status"),
            "last_update": q.get("fetched_at"),
            "message": q.get("message"),
        }

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        sym = normalize_symbol(symbol)
        if sym != self.instrument:
            return {
                "symbol": sym,
                "bid": None,
                "ask": None,
                "mid": None,
                "change": None,
                "source": self.label,
                "status": "needs_config",
                "freshness": None,
                "fetched_at": _now(),
                "message": f"{sym}: этот источник обслуживает {self.instrument}",
            }
        try:
            range_ = "1d" if self.quote_interval in {"1m", "2m", "5m", "15m"} else "5d"
            result = await fetch_yahoo_chart(self.yahoo_symbol, interval=self.quote_interval, range_=range_)
            meta = result.get("meta") or {}
            price = meta.get("regularMarketPrice")
            if price is None:
                raise RuntimeError("no regularMarketPrice")
            mid = format_yahoo_mid(self.instrument, float(price))
            prev = meta.get("previousClose") or meta.get("chartPreviousClose")
            change = None
            if prev:
                change = f"{(float(price) - float(prev)):.4f}"
            market_time = meta.get("regularMarketTime")
            try:
                market_time_unix = int(market_time) if market_time is not None else None
            except (TypeError, ValueError):
                market_time_unix = None
            return {
                "symbol": self.instrument,
                "bid": mid,
                "ask": mid,
                "mid": mid,
                "change": change,
                "source": self.label,
                "status": "connected",
                "freshness": "yahoo",
                "fetched_at": _now(),
                "market_time": market_time_unix,
                "message": f"Котировка {self.yahoo_symbol}",
            }
        except Exception as exc:
            return {
                "symbol": self.instrument,
                "bid": None,
                "ask": None,
                "mid": None,
                "change": None,
                "source": self.label,
                "status": "error",
                "freshness": None,
                "fetched_at": _now(),
                "market_time": None,
                "message": f"Yahoo недоступен: {exc}",
            }


class EurUsdMarketQuoteProvider(MarketDataProvider):
    """Yahoo EURUSD=X primary; NBU cross is last-resort fallback. Never fabricates."""

    id = "yahoo_eurusd"
    label = "Yahoo Finance (EURUSD=X)"

    def __init__(
        self,
        primary: MarketDataProvider | None = None,
        fallback: MarketDataProvider | None = None,
    ) -> None:
        self._primary = primary or YahooQuoteProvider(instrument="EUR/USD", quote_interval="1m")
        self._fallback = fallback or NbuCrossEurUsdProvider()
        self.id = getattr(self._primary, "id", "yahoo_eurusd")
        self.label = getattr(self._primary, "label", self.label)

    async def status(self) -> dict[str, Any]:
        q = await self.get_quote("EUR/USD")
        return {
            "provider_id": q.get("provider") or self.id,
            "label": q.get("source") or self.label,
            "status": q.get("status"),
            "last_update": q.get("fetched_at"),
            "message": q.get("message"),
        }

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        primary = await self._primary.get_quote(symbol)
        primary.setdefault("provider", getattr(self._primary, "id", "yahoo_eurusd"))
        if primary.get("status") == "connected" and primary.get("mid") is not None:
            return primary
        fallback = await self._fallback.get_quote(symbol)
        fallback.setdefault("provider", getattr(self._fallback, "id", "nbu_cross"))
        if fallback.get("status") == "connected" and fallback.get("mid") is not None:
            fallback["fallback_from"] = primary.get("provider") or getattr(self._primary, "id", "yahoo_eurusd")
            return fallback
        return primary


async def fetch_bars(instrument: str, timeframe: str = "1H") -> dict[str, Any]:
    sym = normalize_symbol(instrument)
    tf_map, supported = _maps_for(sym)
    tf = normalize_timeframe(timeframe, instrument=sym)
    yahoo = YAHOO_SYMBOLS.get(sym)
    base_meta = {
        "symbol": sym,
        "timeframe": tf,
        "supported_timeframes": list(supported),
        "provider": "yahoo",
        "provider_symbol": yahoo,
        "chart_engine": "lightweight_charts",
    }
    if not yahoo:
        return {
            **base_meta,
            "status": "needs_config",
            "message": f"Нет источника баров для {sym}",
            "bars": [],
            "bar_count": 0,
            "chart_ready": False,
        }
    interval, range_ = tf_map.get(tf, ("60m", "10d"))
    try:
        result = await fetch_yahoo_chart(yahoo, interval=interval, range_=range_)
        bars = normalize_yahoo_bars(result, timeframe=tf, instrument=sym)
        if not bars:
            return {
                **base_meta,
                "status": "insufficient_data",
                "message": "Yahoo вернул пустые бары",
                "bars": [],
                "bar_count": 0,
                "chart_ready": False,
                "source": f"Yahoo Finance ({yahoo})",
            }
        last = bars[-1]
        return {
            **base_meta,
            "status": "connected",
            "message": "OK",
            "bars": bars,
            "bar_count": len(bars),
            "chart_ready": True,
            "last_close": last.get("c"),
            "last_bar_at": last.get("t"),
            "source": f"Yahoo Finance ({yahoo})",
            "fetched_at": _now(),
        }
    except Exception as exc:
        return {
            **base_meta,
            "status": "error",
            "message": f"Бары недоступны: {exc}",
            "bars": [],
            "bar_count": 0,
            "chart_ready": False,
            "source": f"Yahoo Finance ({yahoo})",
        }
