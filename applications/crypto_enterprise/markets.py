"""Market data — spot, futures, options, perpetuals, tickers, candles, streams."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.config import DEFAULT_CONFIG
from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MarketData:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.market_types = list(DEFAULT_CONFIG.market_types)

    def register_spot(self, *, symbol: str, base: str, quote: str, exchange_id: str = "") -> dict[str, Any]:
        return self._register_market("spot", self.store.spot_markets, symbol, base, quote, exchange_id)

    def register_futures(
        self,
        *,
        symbol: str,
        base: str,
        quote: str,
        exchange_id: str = "",
        expiry: str = "",
    ) -> dict[str, Any]:
        market = self._register_market(
            "futures", self.store.futures_markets, symbol, base, quote, exchange_id
        )
        market["expiry"] = expiry
        return self.store.futures_markets.save(market["market_id"], market)

    def register_options(
        self,
        *,
        symbol: str,
        base: str,
        quote: str,
        exchange_id: str = "",
        option_type: str = "call",
    ) -> dict[str, Any]:
        if option_type not in ("call", "put"):
            raise ValidationError("option_type must be call or put")
        market = self._register_market(
            "options", self.store.options_markets, symbol, base, quote, exchange_id
        )
        market["option_type"] = option_type
        return self.store.options_markets.save(market["market_id"], market)

    def register_perpetual(
        self,
        *,
        symbol: str,
        base: str,
        quote: str,
        exchange_id: str = "",
    ) -> dict[str, Any]:
        return self._register_market(
            "perpetual", self.store.perpetual_markets, symbol, base, quote, exchange_id
        )

    def _register_market(
        self,
        market_type: str,
        bucket: Any,
        symbol: str,
        base: str,
        quote: str,
        exchange_id: str,
    ) -> dict[str, Any]:
        if not symbol or not base or not quote:
            raise ValidationError("symbol, base, and quote required")
        mid = _id("ce_mkt")
        return bucket.save(
            mid,
            {
                "market_id": mid,
                "market_type": market_type,
                "symbol": symbol.upper(),
                "base": base.upper(),
                "quote": quote.upper(),
                "exchange_id": exchange_id,
                "created_at": _now(),
            },
        )

    def ticker(
        self,
        *,
        symbol: str,
        last: float,
        bid: float = 0.0,
        ask: float = 0.0,
        volume: float = 0.0,
    ) -> dict[str, Any]:
        if not symbol:
            raise ValidationError("symbol required")
        tid = _id("ce_tkr")
        return self.store.tickers.save(
            tid,
            {
                "ticker_id": tid,
                "symbol": symbol.upper(),
                "last": float(last),
                "bid": float(bid),
                "ask": float(ask),
                "volume": float(volume),
                "at": _now(),
            },
        )

    def candle(
        self,
        *,
        symbol: str,
        interval: str,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float = 0.0,
    ) -> dict[str, Any]:
        if not symbol or not interval:
            raise ValidationError("symbol and interval required")
        cid = _id("ce_cdl")
        return self.store.candles.save(
            cid,
            {
                "candle_id": cid,
                "symbol": symbol.upper(),
                "interval": interval,
                "open": float(open_),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume),
                "at": _now(),
            },
        )

    def historical(
        self,
        *,
        symbol: str,
        from_ts: str,
        to_ts: str,
        bars: int = 0,
    ) -> dict[str, Any]:
        if not symbol:
            raise ValidationError("symbol required")
        hid = _id("ce_hist")
        return self.store.historical.save(
            hid,
            {
                "history_id": hid,
                "symbol": symbol.upper(),
                "from_ts": from_ts,
                "to_ts": to_ts,
                "bars": int(bars),
                "at": _now(),
            },
        )

    def stream(self, *, symbol: str, channel: str = "trades") -> dict[str, Any]:
        if not symbol:
            raise ValidationError("symbol required")
        sid = _id("ce_strm")
        return self.store.streams.save(
            sid,
            {
                "stream_id": sid,
                "symbol": symbol.upper(),
                "channel": channel,
                "active": True,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "spot": self.store.spot_markets.count(),
            "futures": self.store.futures_markets.count(),
            "options": self.store.options_markets.count(),
            "perpetual": self.store.perpetual_markets.count(),
            "tickers": self.store.tickers.count(),
            "candles": self.store.candles.count(),
            "streams": self.store.streams.count(),
        }
