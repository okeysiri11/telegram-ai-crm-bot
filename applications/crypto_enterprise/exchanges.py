"""Exchange integration — registry, API keys, multi-exchange connectors."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.config import DEFAULT_CONFIG
from applications.crypto_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ExchangeIntegration:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.supported = list(DEFAULT_CONFIG.supported_exchanges)

    def register_exchange(
        self,
        *,
        name: str,
        exchange_code: str,
        region: str = "global",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("exchange name required")
        code = exchange_code.lower().strip()
        if code not in self.supported:
            raise ValidationError(f"exchange_code must be one of {self.supported}")
        eid = _id("ce_ex")
        return self.store.exchanges.save(
            eid,
            {
                "exchange_id": eid,
                "name": name,
                "exchange_code": code,
                "region": region,
                "status": "registered",
                "created_at": _now(),
            },
        )

    def store_api_key(
        self,
        *,
        exchange_id: str,
        label: str,
        api_key_ref: str,
        permissions: list[str] | None = None,
    ) -> dict[str, Any]:
        if self.store.exchanges.get(exchange_id) is None:
            raise NotFoundError("exchange", exchange_id)
        if not api_key_ref:
            raise ValidationError("api_key_ref required")
        kid = _id("ce_key")
        return self.store.api_keys.save(
            kid,
            {
                "key_id": kid,
                "exchange_id": exchange_id,
                "label": label,
                "api_key_ref": api_key_ref,
                "permissions": permissions or ["read"],
                "created_at": _now(),
            },
        )

    def connect(self, *, exchange_id: str, mode: str = "read_only") -> dict[str, Any]:
        exchange = self.store.exchanges.get(exchange_id)
        if exchange is None:
            raise NotFoundError("exchange", exchange_id)
        cid = _id("ce_conn")
        exchange["status"] = "connected"
        self.store.exchanges.save(exchange_id, exchange)
        return self.store.exchange_connections.save(
            cid,
            {
                "connection_id": cid,
                "exchange_id": exchange_id,
                "exchange_code": exchange["exchange_code"],
                "mode": mode,
                "connected": True,
                "at": _now(),
            },
        )

    def integrate_binance(self, *, name: str = "Binance") -> dict[str, Any]:
        return self._integrate("binance", name)

    def integrate_bybit(self, *, name: str = "Bybit") -> dict[str, Any]:
        return self._integrate("bybit", name)

    def integrate_okx(self, *, name: str = "OKX") -> dict[str, Any]:
        return self._integrate("okx", name)

    def integrate_kraken(self, *, name: str = "Kraken") -> dict[str, Any]:
        return self._integrate("kraken", name)

    def integrate_htx(self, *, name: str = "HTX") -> dict[str, Any]:
        return self._integrate("htx", name)

    def integrate_coinbase(self, *, name: str = "Coinbase") -> dict[str, Any]:
        return self._integrate("coinbase", name)

    def _integrate(self, code: str, name: str) -> dict[str, Any]:
        exchange = self.register_exchange(name=name, exchange_code=code)
        key = self.store_api_key(
            exchange_id=exchange["exchange_id"],
            label=f"{code}-primary",
            api_key_ref=f"vault://{code}/primary",
            permissions=["read", "trade"],
        )
        conn = self.connect(exchange_id=exchange["exchange_id"])
        return {
            "exchange": exchange,
            "api_key": key,
            "connection": conn,
            "exchange_code": code,
        }

    def status(self) -> dict[str, Any]:
        return {
            "exchanges": self.store.exchanges.count(),
            "api_keys": self.store.api_keys.count(),
            "connections": self.store.exchange_connections.count(),
            "supported": self.supported,
        }
