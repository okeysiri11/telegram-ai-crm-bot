"""Yahoo Finance chart feed for EURUSD bars and DXY — no fabricated prices."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import aiohttp

from services.fx_market_intel.providers import MarketDataProvider, _now
from services.fx_market_intel.symbols import normalize_symbol

YAHOO_SYMBOLS = {
    "EUR/USD": "EURUSD=X",
    "DXY": "DX-Y.NYB",
}

_TF_MAP = {
    "15m": ("15m", "5d"),
    "15M": ("15m", "5d"),
    "1h": ("60m", "10d"),
    "1H": ("60m", "10d"),
    "4h": ("60m", "30d"),
    "4H": ("60m", "30d"),
    "1d": ("1d", "6mo"),
    "1D": ("1d", "6mo"),
}

SUPPORTED_TIMEFRAMES = ("15m", "1H", "4H", "1D")

_HEADERS = {"User-Agent": "ADOS-FX-Intel/50.7"}


def normalize_timeframe(timeframe: str) -> str:
    raw = (timeframe or "1H").strip()
    key = raw if raw in _TF_MAP else raw.upper() if raw.upper() in _TF_MAP else raw.lower()
    if key not in _TF_MAP:
        return "1H"
    # Canonical labels for API/UI
    canon = {"15m": "15m", "15M": "15m", "1h": "1H", "1H": "1H", "4h": "4H", "4H": "4H", "1d": "1D", "1D": "1D"}
    return canon.get(key, "1H")


async def fetch_yahoo_chart(symbol_yahoo: str, *, interval: str, range_: str) -> dict[str, Any]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol_yahoo}"
    params = {"interval": interval, "range": range_}
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Yahoo HTTP {resp.status}")
            data = await resp.json(content_type=None)
    err = (data.get("chart") or {}).get("error")
    if err:
        raise RuntimeError(str(err))
    results = (data.get("chart") or {}).get("result") or []
    if not results:
        raise RuntimeError("Yahoo empty result")
    return results[0]


def normalize_yahoo_bars(result: dict[str, Any], *, timeframe: str) -> list[dict[str, Any]]:
    ts = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    bars: list[dict[str, Any]] = []
    for i, t in enumerate(ts):
        c = closes[i] if i < len(closes) else None
        if c is None:
            continue
        o = opens[i] if i < len(opens) and opens[i] is not None else c
        h = highs[i] if i < len(highs) and highs[i] is not None else c
        l = lows[i] if i < len(lows) and lows[i] is not None else c
        v = volumes[i] if i < len(volumes) else None
        bars.append(
            {
                "t": datetime.fromtimestamp(int(t), tz=timezone.utc).isoformat(),
                "o": float(o),
                "h": float(h),
                "l": float(l),
                "c": float(c),
                "v": float(v) if v is not None else None,
                "timeframe": timeframe,
            }
        )
    if timeframe.upper() == "4H" and bars:
        # Resample 1h → 4h buckets
        buckets: dict[str, dict[str, Any]] = {}
        for b in bars:
            dt = datetime.fromisoformat(b["t"])
            key_h = (dt.hour // 4) * 4
            key = dt.replace(hour=key_h, minute=0, second=0, microsecond=0).isoformat()
            cur = buckets.get(key)
            if not cur:
                buckets[key] = {**b, "t": key}
            else:
                cur["h"] = max(cur["h"], b["h"])
                cur["l"] = min(cur["l"], b["l"])
                cur["c"] = b["c"]
                if b.get("v") is not None:
                    cur["v"] = (cur.get("v") or 0) + b["v"]
        bars = [buckets[k] for k in sorted(buckets)]
    return bars


class YahooQuoteProvider(MarketDataProvider):
    """Live quote from Yahoo chart meta.regularMarketPrice."""

    def __init__(self, *, instrument: str, label: str | None = None) -> None:
        self.instrument = normalize_symbol(instrument)
        yahoo = YAHOO_SYMBOLS.get(self.instrument)
        if not yahoo:
            raise ValueError(f"Unsupported Yahoo instrument: {instrument}")
        self.yahoo_symbol = yahoo
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
            result = await fetch_yahoo_chart(self.yahoo_symbol, interval="1d", range_="5d")
            meta = result.get("meta") or {}
            price = meta.get("regularMarketPrice")
            if price is None:
                raise RuntimeError("no regularMarketPrice")
            mid = f"{float(price):.4f}" if self.instrument == "EUR/USD" else f"{float(price):.3f}"
            prev = meta.get("previousClose") or meta.get("chartPreviousClose")
            change = None
            if prev:
                change = f"{(float(price) - float(prev)):.4f}"
            return {
                "symbol": self.instrument,
                "bid": mid,
                "ask": mid,
                "mid": mid,
                "change": change,
                "source": self.label,
                "status": "connected",
                "freshness": "live_yahoo",
                "fetched_at": _now(),
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
                "message": f"Yahoo недоступен: {exc}",
            }


async def fetch_bars(instrument: str, timeframe: str = "1H") -> dict[str, Any]:
    sym = normalize_symbol(instrument)
    tf = normalize_timeframe(timeframe)
    yahoo = YAHOO_SYMBOLS.get(sym)
    base_meta = {
        "symbol": sym,
        "timeframe": tf,
        "supported_timeframes": list(SUPPORTED_TIMEFRAMES),
        "provider": "yahoo",
        "provider_symbol": yahoo,
        "chart_engine": "lightweight_charts" if sym == "DXY" else "tradingview_or_native",
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
    interval, range_ = _TF_MAP.get(tf, ("60m", "10d"))
    try:
        result = await fetch_yahoo_chart(yahoo, interval=interval, range_=range_)
        bars = normalize_yahoo_bars(result, timeframe=tf)
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
