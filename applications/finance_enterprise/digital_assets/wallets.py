"""Crypto wallet management — hot/cold/multisig/HD, addresses, balances."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CryptoWalletManagement:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.wallet_types = list(DEFAULT_CONFIG.da_wallet_types)
        self.networks = list(DEFAULT_CONFIG.da_networks)

    def create_wallet(
        self,
        *,
        label: str,
        wallet_type: str = "hot",
        network: str = "ethereum",
        owner_ref: str = "",
    ) -> dict[str, Any]:
        wt = wallet_type.lower().strip()
        if wt not in self.wallet_types:
            raise ValidationError(f"wallet_type must be one of {self.wallet_types}")
        net = network.lower().strip()
        if net not in self.networks:
            raise ValidationError(f"network must be one of {self.networks}")
        if not label:
            raise ValidationError("label required")
        wid = _id("da_wal")
        wallet = self.store.da_wallets.save(
            wid,
            {
                "wallet_id": wid,
                "label": label,
                "wallet_type": wt,
                "network": net,
                "owner_ref": owner_ref,
                "balance": 0.0,
                "created_at": _now(),
            },
        )
        self.store.da_wallet_balances.save(
            wid,
            {"wallet_id": wid, "balance": 0.0, "asset": "NATIVE", "updated_at": _now()},
        )
        return wallet

    def add_address(self, *, wallet_id: str, address: str, derivation_path: str = "") -> dict[str, Any]:
        if self.store.da_wallets.get(wallet_id) is None:
            raise NotFoundError("wallet", wallet_id)
        if not address:
            raise ValidationError("address required")
        aid = _id("da_addr")
        return self.store.da_addresses.save(
            aid,
            {
                "address_id": aid,
                "wallet_id": wallet_id,
                "address": address,
                "derivation_path": derivation_path,
                "at": _now(),
            },
        )

    def update_balance(
        self, *, wallet_id: str, balance: float, asset: str = "NATIVE"
    ) -> dict[str, Any]:
        wallet = self.store.da_wallets.get(wallet_id)
        if wallet is None:
            raise NotFoundError("wallet", wallet_id)
        bal = float(balance)
        if bal < 0:
            raise ValidationError("balance must be non-negative")
        wallet["balance"] = bal
        wallet["updated_at"] = _now()
        self.store.da_wallets.save(wallet_id, wallet)
        return self.store.da_wallet_balances.save(
            wallet_id,
            {"wallet_id": wallet_id, "balance": bal, "asset": asset.upper(), "updated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {
            "wallets": self.store.da_wallets.count(),
            "addresses": self.store.da_addresses.count(),
            "balances": self.store.da_wallet_balances.count(),
            "types": self.wallet_types,
        }
