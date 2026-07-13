# Reference-only market connectors for Dealer Quote Authority Engine.

from __future__ import annotations

from decimal import Decimal
from typing import Any

import aiohttp

from database.models.dealer_quote_authority_engine import QuotePair, ReferenceSourceCode


class ReferenceConnectorError(Exception):
    pass


def _mid(bid: Decimal, ask: Decimal) -> Decimal:
    return (bid + ask) / Decimal("2")


async def fetch_nbu_usd_eur(session: aiohttp.ClientSession) -> dict[str, dict[str, Decimal]]:
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
        resp.raise_for_status()
        rows = await resp.json()
    rates: dict[str, Decimal] = {}
    for row in rows:
        cc = row.get("cc")
        if cc in {"USD", "EUR"}:
            rates[cc] = Decimal(str(row["rate"]))
    if "USD" not in rates:
        raise ReferenceConnectorError("NBU USD rate missing")
    out: dict[str, dict[str, Decimal]] = {}
    usd = rates["USD"]
    out[QuotePair.USD_UAH.value] = {"bid": usd, "ask": usd, "mid": usd}
    if "EUR" in rates:
        eur = rates["EUR"]
        out[QuotePair.EUR_UAH.value] = {"bid": eur, "ask": eur, "mid": eur}
    return out


async def fetch_privatbank(session: aiohttp.ClientSession) -> dict[str, dict[str, Decimal]]:
    url = "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
        resp.raise_for_status()
        rows = await resp.json()
    out: dict[str, dict[str, Decimal]] = {}
    for row in rows:
        ccy = row.get("ccy")
        base = row.get("base_ccy")
        if base != "UAH":
            continue
        bid = Decimal(str(row.get("buy") or row.get("buy/s") or row.get("buy/sale") or 0))
        ask = Decimal(str(row.get("sale") or row.get("sell") or 0))
        if ccy == "USD" and bid > 0 and ask > 0:
            out[QuotePair.USD_UAH.value] = {"bid": bid, "ask": ask, "mid": _mid(bid, ask)}
        if ccy == "EUR" and bid > 0 and ask > 0:
            out[QuotePair.EUR_UAH.value] = {"bid": bid, "ask": ask, "mid": _mid(bid, ask)}
    return out


async def fetch_monobank(session: aiohttp.ClientSession) -> dict[str, dict[str, Decimal]]:
    url = "https://api.monobank.ua/bank/currency"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
        resp.raise_for_status()
        rows = await resp.json()
    out: dict[str, dict[str, Decimal]] = {}
    for row in rows:
        ccy_a = row.get("currencyCodeA")
        ccy_b = row.get("currencyCodeB")
        if ccy_b != 980:
            continue
        rate_buy = Decimal(str(row.get("rateBuy", 0)))
        rate_sell = Decimal(str(row.get("rateSell", 0)))
        if ccy_a == 840 and rate_buy > 0 and rate_sell > 0:
            out[QuotePair.USD_UAH.value] = {
                "bid": rate_buy,
                "ask": rate_sell,
                "mid": _mid(rate_buy, rate_sell),
            }
        if ccy_a == 978 and rate_buy > 0 and rate_sell > 0:
            out[QuotePair.EUR_UAH.value] = {
                "bid": rate_buy,
                "ask": rate_sell,
                "mid": _mid(rate_buy, rate_sell),
            }
    return out


async def fetch_whitebit_usdt(session: aiohttp.ClientSession) -> dict[str, dict[str, Decimal]]:
    async with session.get(
        "https://whitebit.com/api/v4/public/ticker",
        params={"market": "USDT_UAH"},
        timeout=aiohttp.ClientTimeout(total=12),
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
    bid = Decimal(str(data["bid"]))
    ask = Decimal(str(data["ask"]))
    return {
        QuotePair.USDT_UAH.value: {"bid": bid, "ask": ask, "mid": _mid(bid, ask)},
    }


async def fetch_okx_usdt(session: aiohttp.ClientSession) -> dict[str, dict[str, Decimal]]:
    async with session.get(
        "https://www.okx.com/api/v5/market/ticker",
        params={"instId": "USDT-UAH"},
        timeout=aiohttp.ClientTimeout(total=12),
    ) as resp:
        resp.raise_for_status()
        payload = await resp.json()
    items = payload.get("data") or []
    if not items:
        raise ReferenceConnectorError("OKX USDT-UAH empty")
    item = items[0]
    bid = Decimal(str(item.get("bidPx") or item.get("last") or 0))
    ask = Decimal(str(item.get("askPx") or item.get("last") or 0))
    if bid <= 0 or ask <= 0:
        last = Decimal(str(item.get("last", 0)))
        bid = ask = last
    return {
        QuotePair.USDT_UAH.value: {"bid": bid, "ask": ask, "mid": _mid(bid, ask)},
    }


async def fetch_bybit_usdt(session: aiohttp.ClientSession) -> dict[str, dict[str, Decimal]]:
    async with session.get(
        "https://api.bybit.com/v5/market/tickers",
        params={"category": "spot", "symbol": "USDTUAH"},
        timeout=aiohttp.ClientTimeout(total=12),
    ) as resp:
        resp.raise_for_status()
        payload = await resp.json()
    items = payload.get("result", {}).get("list", [])
    if not items:
        raise ReferenceConnectorError("Bybit USDTUAH empty")
    item = items[0]
    bid = Decimal(str(item["bid1Price"]))
    ask = Decimal(str(item["ask1Price"]))
    return {
        QuotePair.USDT_UAH.value: {"bid": bid, "ask": ask, "mid": _mid(bid, ask)},
    }


async def fetch_tradingview_reference(
    session: aiohttp.ClientSession,
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, dict[str, Decimal]]:
    """TradingView connector — uses configured reference levels (reference-only)."""
    from services.tradingview_connector import TradingViewConnector

    return await TradingViewConnector.fetch_reference_quotes(session, config=config)


async def fetch_bank_config_reference(
    source_code: str,
    config: dict[str, Any] | None,
) -> dict[str, dict[str, Decimal]]:
    rates = (config or {}).get("rates") or {}
    out: dict[str, dict[str, Decimal]] = {}
    for pair, values in rates.items():
        bid = Decimal(str(values["bid"]))
        ask = Decimal(str(values["ask"]))
        out[pair] = {"bid": bid, "ask": ask, "mid": _mid(bid, ask)}
    if not out:
        raise ReferenceConnectorError(f"No configured rates for {source_code}")
    return out


REFERENCE_FETCHERS = {
    ReferenceSourceCode.NBU.value: lambda s, cfg: fetch_nbu_usd_eur(s),
    ReferenceSourceCode.PRIVATBANK.value: fetch_privatbank,
    ReferenceSourceCode.MONOBANK.value: fetch_monobank,
    ReferenceSourceCode.WHITEBIT.value: fetch_whitebit_usdt,
    ReferenceSourceCode.OKX.value: fetch_okx_usdt,
    ReferenceSourceCode.BYBIT.value: fetch_bybit_usdt,
    ReferenceSourceCode.TRADINGVIEW.value: fetch_tradingview_reference,
    ReferenceSourceCode.UKRSIBBANK.value: lambda s, cfg: fetch_bank_config_reference(
        ReferenceSourceCode.UKRSIBBANK.value, cfg
    ),
    ReferenceSourceCode.MTB_BANK.value: lambda s, cfg: fetch_bank_config_reference(
        ReferenceSourceCode.MTB_BANK.value, cfg
    ),
    ReferenceSourceCode.OSCHADBANK.value: lambda s, cfg: fetch_bank_config_reference(
        ReferenceSourceCode.OSCHADBANK.value, cfg
    ),
}
