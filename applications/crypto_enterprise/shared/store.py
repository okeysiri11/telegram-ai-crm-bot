"""Shared store — Crypto Enterprise (Sprint 16.0)."""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class EntityStore(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def save(self, key: str, item: T) -> T:
        self._items[key] = item
        return item

    def get(self, key: str) -> T | None:
        return self._items.get(key)

    def delete(self, key: str) -> None:
        self._items.pop(key, None)

    def list_all(self) -> list[T]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)

    def reset(self) -> None:
        self._items.clear()


class CryptoEnterpriseStore:
    def __init__(self) -> None:
        # Exchanges
        self.exchanges: EntityStore = EntityStore()
        self.api_keys: EntityStore = EntityStore()
        self.exchange_connections: EntityStore = EntityStore()
        # Markets
        self.spot_markets: EntityStore = EntityStore()
        self.futures_markets: EntityStore = EntityStore()
        self.options_markets: EntityStore = EntityStore()
        self.perpetual_markets: EntityStore = EntityStore()
        self.tickers: EntityStore = EntityStore()
        self.candles: EntityStore = EntityStore()
        self.historical: EntityStore = EntityStore()
        self.streams: EntityStore = EntityStore()
        # Assets
        self.coins: EntityStore = EntityStore()
        self.tokens: EntityStore = EntityStore()
        self.blockchains: EntityStore = EntityStore()
        self.stablecoins: EntityStore = EntityStore()
        self.pairs: EntityStore = EntityStore()
        # Portfolio
        self.portfolios: EntityStore = EntityStore()
        self.wallets: EntityStore = EntityStore()
        self.allocations: EntityStore = EntityStore()
        self.pnl: EntityStore = EntityStore()
        self.balance_history: EntityStore = EntityStore()
        # Knowledge & dashboards
        self.knowledge: EntityStore = EntityStore()
        self.dashboards: EntityStore = EntityStore()
        # Sprint 16.1 — Technical Analysis / TradingView / Indicators
        self.ta_tv_connections: EntityStore = EntityStore()
        self.ta_watchlists: EntityStore = EntityStore()
        self.ta_chart_sync: EntityStore = EntityStore()
        self.ta_timeframes: EntityStore = EntityStore()
        self.ta_drawings: EntityStore = EntityStore()
        self.ta_alerts: EntityStore = EntityStore()
        self.ta_multi_charts: EntityStore = EntityStore()
        self.ta_charts: EntityStore = EntityStore()
        self.ta_mtf: EntityStore = EntityStore()
        self.ta_playback: EntityStore = EntityStore()
        self.ta_indicators: EntityStore = EntityStore()
        self.ta_structures: EntityStore = EntityStore()
        self.ta_patterns: EntityStore = EntityStore()
        self.ta_ai_trend: EntityStore = EntityStore()
        self.ta_ai_momentum: EntityStore = EntityStore()
        self.ta_ai_volatility: EntityStore = EntityStore()
        self.ta_ai_confluence: EntityStore = EntityStore()
        self.ta_ai_mtf: EntityStore = EntityStore()
        self.ta_ai_signals: EntityStore = EntityStore()
        self.ta_ai_setups: EntityStore = EntityStore()
        self.ta_dashboards: EntityStore = EntityStore()
        self.ta_registries: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


crypto_enterprise_store = CryptoEnterpriseStore()
