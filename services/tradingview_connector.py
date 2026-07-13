# TradingView connector — reference-only market intelligence for Dealer Quote Authority.

from __future__ import annotations

from decimal import Decimal
from typing import Any

import aiohttp

from database.models.dealer_quote_authority_engine import QuotePair


DEFAULT_TRADINGVIEW_SYMBOLS = {
    QuotePair.USD_UAH.value: "FX_IDC:USDUAH",
    QuotePair.EUR_UAH.value: "FX_IDC:EURUAH",
    QuotePair.USDT_UAH.value: "CRYPTO:USDTUAH",
}


class TradingViewConnectorError(Exception):
    pass


class TradingViewConnector:
    @staticmethod
    def _mid(bid: Decimal, ask: Decimal) -> Decimal:
        return (bid + ask) / Decimal("2")

    @staticmethod
    async def fetch_reference_quotes(
        session: aiohttp.ClientSession,
        *,
        config: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Decimal]]:
        """Return configured TradingView reference quotes (reference-only)."""
        cfg = config or {}
        rates = cfg.get("rates") or {}
        if rates:
            out: dict[str, dict[str, Decimal]] = {}
            for pair, values in rates.items():
                bid = Decimal(str(values["bid"]))
                ask = Decimal(str(values["ask"]))
                out[pair] = {
                    "bid": bid,
                    "ask": ask,
                    "mid": TradingViewConnector._mid(bid, ask),
                }
            return out

        symbols = cfg.get("symbols") or DEFAULT_TRADINGVIEW_SYMBOLS
        fallback = cfg.get("fallback_rates") or {}
        out = {}
        for pair, symbol in symbols.items():
            fb = fallback.get(pair)
            if not fb:
                continue
            bid = Decimal(str(fb["bid"]))
            ask = Decimal(str(fb["ask"]))
            out[pair] = {
                "bid": bid,
                "ask": ask,
                "mid": TradingViewConnector._mid(bid, ask),
                "symbol": symbol,
            }
        if not out:
            raise TradingViewConnectorError("TradingView reference not configured")
        return out
