"""Digital wallets — enterprise, customer, vendor, multi-currency balances."""

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


class DigitalWallets:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.wallet_types = list(DEFAULT_CONFIG.pay_wallet_types)

    def create_wallet(
        self,
        *,
        owner_ref: str,
        wallet_type: str = "enterprise",
        currency: str = "USD",
        label: str = "",
    ) -> dict[str, Any]:
        wt = wallet_type.lower().strip()
        if wt not in self.wallet_types:
            raise ValidationError(f"wallet_type must be one of {self.wallet_types}")
        if not owner_ref:
            raise ValidationError("owner_ref required")
        wid = _id("pay_wal")
        ccy = currency.upper()
        wallet = self.store.pay_wallets.save(
            wid,
            {
                "wallet_id": wid,
                "owner_ref": owner_ref,
                "wallet_type": wt,
                "currency": ccy,
                "label": label or f"{wt} wallet",
                "balance": 0.0,
                "created_at": _now(),
            },
        )
        self.store.pay_wallet_balances.save(
            wid,
            {"wallet_id": wid, "currency": ccy, "balance": 0.0, "updated_at": _now()},
        )
        return wallet

    def credit(self, *, wallet_id: str, amount: float, memo: str = "") -> dict[str, Any]:
        return self._mutate(wallet_id=wallet_id, amount=abs(float(amount)), direction="credit", memo=memo)

    def debit(self, *, wallet_id: str, amount: float, memo: str = "") -> dict[str, Any]:
        return self._mutate(wallet_id=wallet_id, amount=abs(float(amount)), direction="debit", memo=memo)

    def _mutate(
        self, *, wallet_id: str, amount: float, direction: str, memo: str
    ) -> dict[str, Any]:
        wallet = self.store.pay_wallets.get(wallet_id)
        if wallet is None:
            raise NotFoundError("wallet", wallet_id)
        if amount <= 0:
            raise ValidationError("amount must be positive")
        bal = float(wallet.get("balance", 0))
        if direction == "debit" and bal < amount:
            raise ValidationError("insufficient wallet balance")
        new_bal = bal + amount if direction == "credit" else bal - amount
        wallet["balance"] = new_bal
        wallet["updated_at"] = _now()
        self.store.pay_wallets.save(wallet_id, wallet)
        self.store.pay_wallet_balances.save(
            wallet_id,
            {
                "wallet_id": wallet_id,
                "currency": wallet["currency"],
                "balance": new_bal,
                "updated_at": _now(),
            },
        )
        hid = _id("pay_wh")
        return self.store.pay_wallet_history.save(
            hid,
            {
                "history_id": hid,
                "wallet_id": wallet_id,
                "direction": direction,
                "amount": amount,
                "balance_after": new_bal,
                "memo": memo,
                "at": _now(),
            },
        )

    def balance(self, *, wallet_id: str) -> dict[str, Any]:
        bal = self.store.pay_wallet_balances.get(wallet_id)
        if bal is None:
            raise NotFoundError("wallet_balance", wallet_id)
        return bal

    def status(self) -> dict[str, Any]:
        return {
            "wallets": self.store.pay_wallets.count(),
            "balances": self.store.pay_wallet_balances.count(),
            "history": self.store.pay_wallet_history.count(),
            "types": self.wallet_types,
        }
