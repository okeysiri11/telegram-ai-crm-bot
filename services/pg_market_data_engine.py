# Market Data Engine v1 — centralized quote collection and distribution.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import aiohttp

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.market_data import (
    SUPPORTED_ASSETS,
    MarketSourceCode,
    MarketSourceType,
    MarketSnapshotType,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.market_data_repository import (
    MarketOrderbookRepository,
    MarketQuoteRepository,
    MarketSnapshotRepository,
    MarketSourceRepository,
    MarketSpreadRepository,
)
from repositories.user_role_repository import UserRoleRepository

MARKET_DATA_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER", "ACCOUNTANT"})

EXCHANGE_CRYPTO_ASSETS = frozenset({"BTC", "ETH", "USDT"})

BINANCE_SYMBOLS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "USDT": "USDCUSDT",
}

BYBIT_SYMBOLS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
}

WHITEBIT_SYMBOLS = {
    "BTC": "BTC_USDT",
    "ETH": "ETH_USDT",
}

DEFAULT_FX_RATES: dict[str, dict[str, str]] = {
    "USD": {"bid": "1.0", "ask": "1.0", "last": "1.0", "volume_24h": "0"},
    "EUR": {"bid": "1.08", "ask": "1.09", "last": "1.085", "volume_24h": "0"},
    "AED": {"bid": "0.272", "ask": "0.273", "last": "0.2725", "volume_24h": "0"},
    "PLN": {"bid": "0.25", "ask": "0.251", "last": "0.2505", "volume_24h": "0"},
    "GEL": {"bid": "0.37", "ask": "0.371", "last": "0.3705", "volume_24h": "0"},
}

DEFAULT_METALS_RATES: dict[str, dict[str, str]] = {
    "XAU": {"bid": "2650", "ask": "2655", "last": "2652.5", "volume_24h": "0"},
    "XAG": {"bid": "31.2", "ask": "31.4", "last": "31.3", "volume_24h": "0"},
}


class MarketDataEngineError(Exception):
    pass


class MarketDataEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in MARKET_DATA_ROLES for role in roles)

    @staticmethod
    async def _audit(
        session,
        *,
        user_id: int,
        action: str,
        entity_id: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=user_id,
            entity_type="market",
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def _publish_event(
        event_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from services import crm_event_bus as bus

            await bus.publish_event(
                event_type,
                "market",
                aggregate_id,
                payload,
            )
        except Exception:
            pass

    @staticmethod
    def _spread_values(bid: Decimal, ask: Decimal) -> tuple[Decimal, Decimal, Decimal]:
        spread_abs = ask - bid
        mid = (bid + ask) / Decimal("2")
        spread_pct = (spread_abs / mid * Decimal("100")) if mid > 0 else Decimal("0")
        return spread_abs, mid, spread_pct.quantize(Decimal("0.000001"))

    @staticmethod
    def _aggregate_bid_ask(quotes: list) -> tuple[Decimal, Decimal, Any | None]:
        if not quotes:
            raise MarketDataEngineError("No quotes available")
        best_bid_quote = max(quotes, key=lambda q: q.bid)
        best_ask_quote = min(quotes, key=lambda q: q.ask)
        if best_bid_quote.bid < best_ask_quote.ask:
            return best_bid_quote.bid, best_ask_quote.ask, None
        same_source = min(
            quotes,
            key=lambda q: q.spread if q.spread > 0 else Decimal("999999999"),
        )
        return same_source.bid, same_source.ask, same_source

    @staticmethod
    def _quote_payload(quote) -> dict[str, str]:
        return {
            "asset": quote.asset,
            "bid": str(quote.bid),
            "ask": str(quote.ask),
            "last": str(quote.last),
            "spread": str(quote.spread),
            "volume_24h": str(quote.volume_24h or 0),
            "quoted_at": quote.quoted_at.isoformat(),
        }

    @staticmethod
    async def _fetch_binance(session_http: aiohttp.ClientSession, symbol: str) -> dict:
        async with session_http.get(
            "https://api.binance.com/api/v3/ticker/bookTicker",
            params={"symbol": symbol},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        async with session_http.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": symbol},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()
            stats = await resp.json()
        bid = Decimal(data["bidPrice"])
        ask = Decimal(data["askPrice"])
        last = Decimal(stats.get("lastPrice", data["bidPrice"]))
        volume = Decimal(stats.get("volume", "0"))
        return {"bid": bid, "ask": ask, "last": last, "volume_24h": volume, "symbol": symbol}

    @staticmethod
    async def _fetch_binance_orderbook(
        session_http: aiohttp.ClientSession,
        symbol: str,
        depth: int = 5,
    ) -> dict:
        async with session_http.get(
            "https://api.binance.com/api/v3/depth",
            params={"symbol": symbol, "limit": depth},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return {"bids": data.get("bids", [])[:depth], "asks": data.get("asks", [])[:depth]}

    @staticmethod
    async def _fetch_bybit(session_http: aiohttp.ClientSession, symbol: str) -> dict:
        async with session_http.get(
            "https://api.bybit.com/v5/market/tickers",
            params={"category": "spot", "symbol": symbol},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()
            payload = await resp.json()
        items = payload.get("result", {}).get("list", [])
        if not items:
            raise MarketDataEngineError(f"Bybit empty ticker for {symbol}")
        item = items[0]
        bid = Decimal(item["bid1Price"])
        ask = Decimal(item["ask1Price"])
        last = Decimal(item.get("lastPrice", item["bid1Price"]))
        volume = Decimal(item.get("volume24h", "0"))
        return {"bid": bid, "ask": ask, "last": last, "volume_24h": volume, "symbol": symbol}

    @staticmethod
    async def _fetch_whitebit(session_http: aiohttp.ClientSession, symbol: str) -> dict:
        async with session_http.get(
            "https://whitebit.com/api/v4/public/ticker",
            params={"market": symbol},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        bid = Decimal(data["bid"])
        ask = Decimal(data["ask"])
        last = Decimal(data.get("last", data["bid"]))
        volume = Decimal(data.get("volume", "0"))
        return {"bid": bid, "ask": ask, "last": last, "volume_24h": volume, "symbol": symbol}

    @staticmethod
    async def _fetch_exchange_quotes(
        source_code: str,
        session_http: aiohttp.ClientSession,
    ) -> list[dict[str, Any]]:
        symbol_map = {
            MarketSourceCode.BINANCE.value: BINANCE_SYMBOLS,
            MarketSourceCode.BYBIT.value: BYBIT_SYMBOLS,
            MarketSourceCode.WHITEBIT.value: WHITEBIT_SYMBOLS,
        }.get(source_code, {})

        fetchers = {
            MarketSourceCode.BINANCE.value: MarketDataEngineV1._fetch_binance,
            MarketSourceCode.BYBIT.value: MarketDataEngineV1._fetch_bybit,
            MarketSourceCode.WHITEBIT.value: MarketDataEngineV1._fetch_whitebit,
        }
        fetcher = fetchers.get(source_code)
        if fetcher is None:
            return []

        quotes: list[dict[str, Any]] = []
        for asset, symbol in symbol_map.items():
            if asset not in EXCHANGE_CRYPTO_ASSETS:
                continue
            data = await fetcher(session_http, symbol)
            spread_abs, _, _ = MarketDataEngineV1._spread_values(data["bid"], data["ask"])
            quotes.append(
                {
                    "asset": asset,
                    "quote_symbol": symbol,
                    "bid": data["bid"],
                    "ask": data["ask"],
                    "last": data["last"],
                    "spread": spread_abs,
                    "volume_24h": data.get("volume_24h"),
                }
            )
        return quotes

    @staticmethod
    async def _fetch_exchange_orderbooks(
        source_code: str,
        session_http: aiohttp.ClientSession,
    ) -> list[dict[str, Any]]:
        if source_code != MarketSourceCode.BINANCE.value:
            return []

        books: list[dict[str, Any]] = []
        for asset, symbol in BINANCE_SYMBOLS.items():
            if asset not in EXCHANGE_CRYPTO_ASSETS:
                continue
            book = await MarketDataEngineV1._fetch_binance_orderbook(session_http, symbol)
            books.append({"asset": asset, **book})
        return books

    @staticmethod
    def _config_quotes(source, assets: frozenset[str]) -> list[dict[str, Any]]:
        config = source.config or {}
        rates = config.get("rates", {})
        if source.source_code == MarketSourceCode.FX.value and not rates:
            rates = DEFAULT_FX_RATES
        if source.source_code == MarketSourceCode.PRECIOUS_METALS.value and not rates:
            rates = DEFAULT_METALS_RATES

        quotes: list[dict[str, Any]] = []
        for asset in assets:
            rate = rates.get(asset)
            if rate is None:
                continue
            bid = Decimal(str(rate["bid"]))
            ask = Decimal(str(rate["ask"]))
            last = Decimal(str(rate.get("last", rate["bid"])))
            spread_abs, _, _ = MarketDataEngineV1._spread_values(bid, ask)
            quotes.append(
                {
                    "asset": asset,
                    "quote_symbol": asset,
                    "bid": bid,
                    "ask": ask,
                    "last": last,
                    "spread": spread_abs,
                    "volume_24h": Decimal(str(rate.get("volume_24h", "0"))),
                }
            )
        return quotes

    @staticmethod
    async def _sync_pricing(actor_id: int, source_code: str, quote) -> None:
        pricing_sources = {
            MarketSourceCode.BINANCE.value,
            MarketSourceCode.BYBIT.value,
            MarketSourceCode.WHITEBIT.value,
            MarketSourceCode.MANUAL.value,
        }
        if source_code not in pricing_sources:
            return
        if quote.asset not in EXCHANGE_CRYPTO_ASSETS:
            return
        try:
            from services.pg_pricing_engine import PricingEngineV1

            await PricingEngineV1.update_price(
                actor_id,
                source_name=source_code,
                asset=quote.asset,
                bid_price=quote.bid,
                ask_price=quote.ask,
            )
        except Exception:
            pass

    @staticmethod
    async def update_quotes(
        actor_id: int,
        *,
        assets: list[str] | None = None,
    ) -> dict[str, Any]:
        if not await MarketDataEngineV1.user_can_access(actor_id):
            raise MarketDataEngineError("Access denied")

        target_assets = frozenset(assets or SUPPORTED_ASSETS)
        updated: list[dict[str, Any]] = []
        failed_sources: list[str] = []
        spread_changes: list[str] = []

        async with get_session() as session:
            source_repo = MarketSourceRepository(session)
            quote_repo = MarketQuoteRepository(session)
            book_repo = MarketOrderbookRepository(session)
            spread_repo = MarketSpreadRepository(session)
            snapshot_repo = MarketSnapshotRepository(session)
            sources = await source_repo.list_active()

            async with aiohttp.ClientSession() as http:
                for source in sources:
                    try:
                        if source.source_type == MarketSourceType.EXCHANGE.value:
                            raw_quotes = await MarketDataEngineV1._fetch_exchange_quotes(
                                source.source_code, http
                            )
                            raw_books = await MarketDataEngineV1._fetch_exchange_orderbooks(
                                source.source_code, http
                            )
                        else:
                            raw_quotes = MarketDataEngineV1._config_quotes(
                                source, target_assets
                            )
                            raw_books = []

                        source_quotes = []
                        for raw in raw_quotes:
                            if raw["asset"] not in target_assets:
                                continue
                            quote = await quote_repo.upsert(
                                source_id=source.id,
                                asset=raw["asset"],
                                bid=raw["bid"],
                                ask=raw["ask"],
                                last=raw["last"],
                                spread=raw["spread"],
                                volume_24h=raw.get("volume_24h"),
                                quote_symbol=raw.get("quote_symbol"),
                            )
                            source_quotes.append(quote)
                            updated.append(
                                {
                                    "source": source.source_code,
                                    **MarketDataEngineV1._quote_payload(quote),
                                }
                            )

                        for book in raw_books:
                            if book["asset"] not in target_assets:
                                continue
                            await book_repo.create(
                                source_id=source.id,
                                asset=book["asset"],
                                bids=book["bids"],
                                asks=book["asks"],
                            )

                        await source_repo.mark_success(source.id)
                        await MarketDataEngineV1._audit(
                            session,
                            user_id=actor_id,
                            action=AuditAction.QUOTE_UPDATED.value,
                            entity_id=str(source.id),
                            new_value={
                                "source": source.source_code,
                                "quotes": len(source_quotes),
                            },
                        )

                        for quote in source_quotes:
                            await MarketDataEngineV1._sync_pricing(
                                actor_id, source.source_code, quote
                            )

                    except Exception as exc:
                        await source_repo.mark_failure(source.id)
                        failed_sources.append(source.source_code)
                        await MarketDataEngineV1._audit(
                            session,
                            user_id=actor_id,
                            action=AuditAction.SOURCE_FAILED.value,
                            entity_id=str(source.id),
                            new_value={
                                "source": source.source_code,
                                "error": str(exc),
                            },
                        )

            snapshot_payload: dict[str, Any] = {"quotes": updated, "assets": sorted(target_assets)}
            for asset in sorted(target_assets):
                spread = await MarketDataEngineV1.calculate_spread(
                    actor_id,
                    asset,
                    _session=session,
                    _inline=True,
                )
                if spread:
                    old = await spread_repo.latest_for_asset(asset)
                    spread_record = await spread_repo.create(
                        asset=asset,
                        best_bid=Decimal(spread["best_bid"]),
                        best_ask=Decimal(spread["best_ask"]),
                        mid_price=Decimal(spread["mid_price"]),
                        spread_abs=Decimal(spread["spread_abs"]),
                        spread_pct=Decimal(spread["spread_pct"]),
                    )
                    snapshot_payload.setdefault("spreads", []).append(spread)
                    if old and old.spread_pct != spread_record.spread_pct:
                        spread_changes.append(asset)

            await snapshot_repo.create(
                snapshot_type=MarketSnapshotType.FULL.value,
                payload=snapshot_payload,
            )

        aggregate_id = uuid.uuid4()
        if updated:
            await MarketDataEngineV1._publish_event(
                "market.quote.updated",
                aggregate_id,
                {"count": len(updated), "sources": len(sources) - len(failed_sources)},
            )
        for asset in spread_changes:
            await MarketDataEngineV1._publish_event(
                "market.spread.changed",
                aggregate_id,
                {"asset": asset},
            )
        for source_code in failed_sources:
            await MarketDataEngineV1._publish_event(
                "market.source.failed",
                aggregate_id,
                {"source": source_code},
            )

        return {
            "updated": len(updated),
            "failed_sources": failed_sources,
            "spread_changes": spread_changes,
            "quotes": updated,
        }

    @staticmethod
    async def get_best_bid(
        actor_id: int,
        asset: str,
    ) -> dict[str, Any] | None:
        if not await MarketDataEngineV1.user_can_access(actor_id):
            raise MarketDataEngineError("Access denied")

        async with get_session() as session:
            quote = await MarketQuoteRepository(session).best_bid(asset)
            if quote is None:
                return None
            return MarketDataEngineV1._quote_payload(quote)

    @staticmethod
    async def get_best_ask(
        actor_id: int,
        asset: str,
    ) -> dict[str, Any] | None:
        if not await MarketDataEngineV1.user_can_access(actor_id):
            raise MarketDataEngineError("Access denied")

        async with get_session() as session:
            quote = await MarketQuoteRepository(session).best_ask(asset)
            if quote is None:
                return None
            return MarketDataEngineV1._quote_payload(quote)

    @staticmethod
    async def get_mid_price(
        actor_id: int,
        asset: str,
    ) -> dict[str, Any] | None:
        if not await MarketDataEngineV1.user_can_access(actor_id):
            raise MarketDataEngineError("Access denied")

        async with get_session() as session:
            quotes = await MarketQuoteRepository(session).list_by_asset(asset)
            if not quotes:
                return None
            bid, ask, source_quote = MarketDataEngineV1._aggregate_bid_ask(quotes)
            _, mid, spread_pct = MarketDataEngineV1._spread_values(bid, ask)
            return {
                "asset": asset,
                "best_bid": str(bid),
                "best_ask": str(ask),
                "mid_price": str(mid),
                "spread_pct": str(spread_pct),
                "source_id": str(source_quote.source_id) if source_quote else None,
            }

    @staticmethod
    async def calculate_spread(
        actor_id: int,
        asset: str,
        *,
        _session=None,
        _inline: bool = False,
    ) -> dict[str, Any] | None:
        if not _inline and not await MarketDataEngineV1.user_can_access(actor_id):
            raise MarketDataEngineError("Access denied")

        async def _calc(session):
            quotes = await MarketQuoteRepository(session).list_by_asset(asset)
            if not quotes:
                return None
            bid, ask, _ = MarketDataEngineV1._aggregate_bid_ask(quotes)
            spread_abs, mid, spread_pct = MarketDataEngineV1._spread_values(bid, ask)
            return {
                "asset": asset,
                "best_bid": str(bid),
                "best_ask": str(ask),
                "mid_price": str(mid),
                "spread_abs": str(spread_abs),
                "spread_pct": str(spread_pct),
            }

        if _inline:
            return await _calc(_session)

        async with get_session() as session:
            return await _calc(session)

    @staticmethod
    async def set_manual_quote(
        actor_id: int,
        *,
        asset: str,
        bid: Decimal,
        ask: Decimal,
        last: Decimal | None = None,
        volume_24h: Decimal | None = None,
    ) -> dict[str, Any]:
        if not await MarketDataEngineV1.user_can_access(actor_id):
            raise MarketDataEngineError("Access denied")
        if asset not in SUPPORTED_ASSETS:
            raise MarketDataEngineError(f"Unsupported asset: {asset}")

        resolved_last = last or (bid + ask) / Decimal("2")
        spread_abs, _, _ = MarketDataEngineV1._spread_values(bid, ask)

        async with get_session() as session:
            source = await MarketSourceRepository(session).get_by_code(
                MarketSourceCode.MANUAL.value
            )
            if source is None:
                raise MarketDataEngineError("Manual source not configured")

            quote = await MarketQuoteRepository(session).upsert(
                source_id=source.id,
                asset=asset,
                bid=bid,
                ask=ask,
                last=resolved_last,
                spread=spread_abs,
                volume_24h=volume_24h,
                quote_symbol=asset,
            )
            await MarketDataEngineV1._audit(
                session,
                user_id=actor_id,
                action=AuditAction.QUOTE_UPDATED.value,
                entity_id=str(source.id),
                new_value={"asset": asset, "bid": str(bid), "ask": str(ask)},
            )

        await MarketDataEngineV1._sync_pricing(actor_id, MarketSourceCode.MANUAL.value, quote)
        await MarketDataEngineV1._publish_event(
            "market.quote.updated",
            source.id,
            {"asset": asset, "source": MarketSourceCode.MANUAL.value},
        )
        return MarketDataEngineV1._quote_payload(quote)
