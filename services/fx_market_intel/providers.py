"""Market-data / news / macro provider abstractions — no fabricated live feeds."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import aiohttp

from services.fx_market_intel.symbols import normalize_symbol


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class QuoteSnapshot(dict):
    """Typed-ish dict for quotes."""


class MarketDataProvider(ABC):
    id: str
    label: str

    @abstractmethod
    async def status(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_quote(self, symbol: str) -> dict[str, Any]:
        ...


class NullMarketDataProvider(MarketDataProvider):
    id = "null"
    label = "Не подключено"

    async def status(self) -> dict[str, Any]:
        return {
            "provider_id": self.id,
            "label": self.label,
            "status": "not_connected",
            "last_update": None,
            "message": "Источник котировок не настроен",
        }

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        sym = normalize_symbol(symbol)
        return {
            "symbol": sym,
            "bid": None,
            "ask": None,
            "mid": None,
            "change": None,
            "source": self.label,
            "status": "not_connected",
            "freshness": None,
            "fetched_at": _now(),
            "message": "Котировка недоступна — источник не подключён",
        }


class NbuCrossEurUsdProvider(MarketDataProvider):
    """EUR/USD via live NBU EUR/UAH ÷ USD/UAH. Never invents numbers if NBU fails."""

    id = "nbu_cross"
    label = "НБУ (кросс EUR/USD)"

    async def status(self) -> dict[str, Any]:
        q = await self.get_quote("EUR/USD")
        return {
            "provider_id": self.id,
            "label": self.label,
            "status": q.get("status"),
            "last_update": q.get("fetched_at"),
            "message": q.get("message"),
        }

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        sym = normalize_symbol(symbol)
        if sym != "EUR/USD":
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
                "message": f"{sym}: этот источник поддерживает только EUR/USD",
            }
        try:
            from database.models.dealer_quote_authority_engine import QuotePair
            from services.market_reference_connectors import fetch_nbu_usd_eur

            async with aiohttp.ClientSession() as session:
                rates = await fetch_nbu_usd_eur(session)
            usd_row = rates.get(QuotePair.USD_UAH.value)
            eur_row = rates.get(QuotePair.EUR_UAH.value)
            if not usd_row or not eur_row:
                raise ValueError("NBU USD/EUR UAH legs missing")
            usd_mid = Decimal(str(usd_row["mid"]))
            eur_mid = Decimal(str(eur_row["mid"]))
            if usd_mid <= 0:
                raise ValueError("invalid USD mid")
            mid = (eur_mid / usd_mid).quantize(Decimal("0.0001"))
            return {
                "symbol": "EUR/USD",
                "bid": str(mid),
                "ask": str(mid),
                "mid": str(mid),
                "change": None,
                "source": self.label,
                "status": "connected",
                "freshness": "live_nbu_cross",
                "fetched_at": _now(),
                "message": "Кросс из официальных курсов НБУ",
            }
        except Exception as exc:
            return {
                "symbol": "EUR/USD",
                "bid": None,
                "ask": None,
                "mid": None,
                "change": None,
                "source": self.label,
                "status": "error",
                "freshness": None,
                "fetched_at": _now(),
                "message": f"НБУ недоступен: {exc}",
            }


class DxyStubProvider(MarketDataProvider):
    id = "dxy_stub"
    label = "DXY провайдер"

    async def status(self) -> dict[str, Any]:
        return {
            "provider_id": self.id,
            "label": self.label,
            "status": "needs_config",
            "last_update": None,
            "message": "Требуется настройка источника DXY",
        }

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        sym = normalize_symbol(symbol)
        return {
            "symbol": sym if sym == "DXY" else sym,
            "bid": None,
            "ask": None,
            "mid": None,
            "change": None,
            "source": self.label,
            "status": "needs_config",
            "freshness": None,
            "fetched_at": _now(),
            "message": "DXY: внешний индексный провайдер не подключён",
        }


class NewsProvider(ABC):
    @abstractmethod
    async def fetch(self, *, instruments: list[str], limit: int = 20) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def status(self) -> dict[str, Any]:
        ...


class NullNewsProvider(NewsProvider):
    async def status(self) -> dict[str, Any]:
        return {"status": "not_connected", "label": "Новости", "message": "Источник новостей не подключён"}

    async def fetch(self, *, instruments: list[str], limit: int = 20) -> list[dict[str, Any]]:
        return []


class MacroCalendarProvider(ABC):
    @abstractmethod
    async def list_events(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def status(self) -> dict[str, Any]:
        ...


class NullMacroCalendarProvider(MacroCalendarProvider):
    async def status(self) -> dict[str, Any]:
        return {
            "status": "not_connected",
            "label": "Экономический календарь",
            "message": "Календарь макрособытий не подключён",
        }

    async def list_events(self) -> list[dict[str, Any]]:
        return []


def news_fingerprint(title: str, url: str = "", published_at: str = "") -> str:
    raw = f"{(title or '').strip().lower()}|{(url or '').strip().lower()}|{(published_at or '')[:10]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
