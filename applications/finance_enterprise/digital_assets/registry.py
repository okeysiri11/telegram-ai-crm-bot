"""Digital asset registry — assets, tokens, blockchains, wallets, exchanges, custody."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DigitalAssetRegistry:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.networks = list(DEFAULT_CONFIG.da_networks)

    def register_asset(
        self, *, symbol: str, name: str, asset_type: str = "crypto", network: str = "ethereum"
    ) -> dict[str, Any]:
        if not symbol or not name:
            raise ValidationError("symbol and name required")
        net = network.lower().strip()
        if net not in self.networks:
            raise ValidationError(f"network must be one of {self.networks}")
        aid = _id("da_ast")
        return self.store.da_assets.save(
            aid,
            {
                "asset_id": aid,
                "symbol": symbol.upper(),
                "name": name,
                "asset_type": asset_type,
                "network": net,
                "created_at": _now(),
            },
        )

    def register_token(
        self, *, symbol: str, contract: str, network: str = "ethereum", decimals: int = 18
    ) -> dict[str, Any]:
        if not symbol or not contract:
            raise ValidationError("symbol and contract required")
        net = network.lower().strip()
        if net not in self.networks:
            raise ValidationError(f"network must be one of {self.networks}")
        tid = _id("da_tok")
        return self.store.da_tokens.save(
            tid,
            {
                "token_id": tid,
                "symbol": symbol.upper(),
                "contract": contract,
                "network": net,
                "decimals": int(decimals),
                "created_at": _now(),
            },
        )

    def register_blockchain(
        self, *, network: str, chain_id: str = "", native_symbol: str = ""
    ) -> dict[str, Any]:
        net = network.lower().strip()
        if net not in self.networks:
            raise ValidationError(f"network must be one of {self.networks}")
        bid = _id("da_bc")
        return self.store.da_blockchains.save(
            bid,
            {
                "blockchain_id": bid,
                "network": net,
                "chain_id": chain_id or net,
                "native_symbol": native_symbol or net[:3].upper(),
                "created_at": _now(),
            },
        )

    def register_exchange_account(
        self, *, exchange: str, account_ref: str, label: str = ""
    ) -> dict[str, Any]:
        if not exchange or not account_ref:
            raise ValidationError("exchange and account_ref required")
        eid = _id("da_ex")
        return self.store.da_exchange_accounts.save(
            eid,
            {
                "exchange_account_id": eid,
                "exchange": exchange.lower(),
                "account_ref": account_ref,
                "label": label or f"{exchange} account",
                "created_at": _now(),
            },
        )

    def register_custody(
        self, *, provider: str, vault_ref: str, label: str = ""
    ) -> dict[str, Any]:
        if not provider or not vault_ref:
            raise ValidationError("provider and vault_ref required")
        cid = _id("da_cust")
        return self.store.da_custody.save(
            cid,
            {
                "custody_id": cid,
                "provider": provider,
                "vault_ref": vault_ref,
                "label": label or provider,
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "assets": self.store.da_assets.count(),
            "tokens": self.store.da_tokens.count(),
            "blockchains": self.store.da_blockchains.count(),
            "exchange_accounts": self.store.da_exchange_accounts.count(),
            "custody": self.store.da_custody.count(),
            "networks": self.networks,
        }
