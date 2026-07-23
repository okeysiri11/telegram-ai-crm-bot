"""Asset registry — coins, tokens, blockchains, stablecoins, pairs."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AssetRegistry:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def register_coin(self, *, symbol: str, name: str, blockchain_id: str = "") -> dict[str, Any]:
        if not symbol or not name:
            raise ValidationError("symbol and name required")
        cid = _id("ce_coin")
        return self.store.coins.save(
            cid,
            {
                "coin_id": cid,
                "symbol": symbol.upper(),
                "name": name,
                "blockchain_id": blockchain_id,
                "created_at": _now(),
            },
        )

    def register_token(
        self,
        *,
        symbol: str,
        name: str,
        blockchain_id: str,
        contract: str = "",
    ) -> dict[str, Any]:
        if not symbol or not name:
            raise ValidationError("symbol and name required")
        if blockchain_id and self.store.blockchains.get(blockchain_id) is None:
            raise NotFoundError("blockchain", blockchain_id)
        tid = _id("ce_tok")
        return self.store.tokens.save(
            tid,
            {
                "token_id": tid,
                "symbol": symbol.upper(),
                "name": name,
                "blockchain_id": blockchain_id,
                "contract": contract,
                "created_at": _now(),
            },
        )

    def register_blockchain(self, *, name: str, chain_id: str, native_symbol: str = "") -> dict[str, Any]:
        if not name or not chain_id:
            raise ValidationError("name and chain_id required")
        bid = _id("ce_chain")
        return self.store.blockchains.save(
            bid,
            {
                "blockchain_id": bid,
                "name": name,
                "chain_id": chain_id,
                "native_symbol": native_symbol.upper(),
                "created_at": _now(),
            },
        )

    def register_stablecoin(
        self,
        *,
        symbol: str,
        name: str,
        peg: str = "USD",
        blockchain_id: str = "",
    ) -> dict[str, Any]:
        if not symbol or not name:
            raise ValidationError("symbol and name required")
        sid = _id("ce_stab")
        return self.store.stablecoins.save(
            sid,
            {
                "stablecoin_id": sid,
                "symbol": symbol.upper(),
                "name": name,
                "peg": peg.upper(),
                "blockchain_id": blockchain_id,
                "created_at": _now(),
            },
        )

    def register_pair(self, *, base: str, quote: str, symbol: str = "") -> dict[str, Any]:
        if not base or not quote:
            raise ValidationError("base and quote required")
        pair_symbol = symbol.upper() if symbol else f"{base.upper()}/{quote.upper()}"
        pid = _id("ce_pair")
        return self.store.pairs.save(
            pid,
            {
                "pair_id": pid,
                "base": base.upper(),
                "quote": quote.upper(),
                "symbol": pair_symbol,
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "coins": self.store.coins.count(),
            "tokens": self.store.tokens.count(),
            "blockchains": self.store.blockchains.count(),
            "stablecoins": self.store.stablecoins.count(),
            "pairs": self.store.pairs.count(),
        }
