# Escrow Engine — secure hold, release, fraud protection, disputes.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transactions.models import EscrowAccount, EscrowStatus


class EscrowEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def open(
        self,
        *,
        transaction_id: str,
        amount: float,
        currency: str = "USD",
        release_conditions: list[str] | None = None,
    ) -> EscrowAccount:
        if amount <= 0:
            raise ValidationError("amount must be positive")
        account = EscrowAccount(
            transaction_id=transaction_id,
            amount=amount,
            currency=currency,
            status=EscrowStatus.OPEN,
            release_conditions=release_conditions
            or ["payment_cleared", "contract_signed", "no_active_dispute"],
        )
        return self._store.escrow_accounts.save(account.escrow_id, account)

    def get(self, escrow_id: str) -> EscrowAccount:
        account = self._store.escrow_accounts.get(escrow_id)
        if account is None:
            raise NotFoundError("EscrowAccount", escrow_id)
        return account

    def hold(self, escrow_id: str) -> EscrowAccount:
        account = self.get(escrow_id)
        account.status = EscrowStatus.HOLDING
        return self._store.escrow_accounts.save(escrow_id, account)

    def release(self, escrow_id: str, *, conditions_met: list[str] | None = None) -> EscrowAccount:
        account = self.get(escrow_id)
        if account.status == EscrowStatus.DISPUTED:
            raise ValidationError("cannot release while disputed")
        met = set(conditions_met or account.release_conditions)
        required = set(account.release_conditions)
        if not required.issubset(met):
            raise ValidationError(f"release conditions not met: {sorted(required - met)}")
        account.status = EscrowStatus.RELEASED
        return self._store.escrow_accounts.save(escrow_id, account)

    def refund(self, escrow_id: str) -> EscrowAccount:
        account = self.get(escrow_id)
        account.status = EscrowStatus.REFUNDED
        return self._store.escrow_accounts.save(escrow_id, account)

    def dispute(self, escrow_id: str, reason: str, opened_by: str = "") -> EscrowAccount:
        account = self.get(escrow_id)
        account.status = EscrowStatus.DISPUTED
        account.disputes.append({"reason": reason, "opened_by": opened_by, "at": time.time(), "status": "open"})
        return self._store.escrow_accounts.save(escrow_id, account)

    def resolve_dispute(self, escrow_id: str, resolution: str = "release") -> EscrowAccount:
        account = self.get(escrow_id)
        if account.disputes:
            account.disputes[-1]["status"] = "resolved"
            account.disputes[-1]["resolution"] = resolution
        if resolution == "refund":
            account.status = EscrowStatus.REFUNDED
        else:
            account.status = EscrowStatus.HOLDING
        return self._store.escrow_accounts.save(escrow_id, account)

    def metrics(self) -> dict:
        items = self._store.escrow_accounts.list_all()
        return {
            "escrow_accounts": len(items),
            "holding": len([a for a in items if a.status == EscrowStatus.HOLDING]),
            "disputed": len([a for a in items if a.status == EscrowStatus.DISPUTED]),
        }


escrow_engine = EscrowEngine()
