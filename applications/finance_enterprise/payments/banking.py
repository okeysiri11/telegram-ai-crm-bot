"""Banking — bank registry, accounts, IBAN/SWIFT, statements."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Banking:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def register_bank(
        self, *, name: str, country: str = "", bic: str = "", swift: str = ""
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("bank name required")
        bid = _id("pay_bank")
        return self.store.pay_banks.save(
            bid,
            {
                "bank_id": bid,
                "name": name,
                "country": country,
                "bic": bic,
                "swift": swift or bic,
                "created_at": _now(),
            },
        )

    def register_account(
        self,
        *,
        bank_id: str,
        account_name: str,
        iban: str = "",
        currency: str = "USD",
        organization_id: str = "",
    ) -> dict[str, Any]:
        if self.store.pay_banks.get(bank_id) is None:
            raise NotFoundError("bank", bank_id)
        if not account_name:
            raise ValidationError("account_name required")
        aid = _id("pay_ba")
        return self.store.pay_bank_accounts.save(
            aid,
            {
                "bank_account_id": aid,
                "bank_id": bank_id,
                "account_name": account_name,
                "iban": iban,
                "currency": currency.upper(),
                "organization_id": organization_id,
                "verified": False,
                "created_at": _now(),
            },
        )

    def set_iban(self, *, bank_account_id: str, iban: str) -> dict[str, Any]:
        acct = self.store.pay_bank_accounts.get(bank_account_id)
        if acct is None:
            raise NotFoundError("bank_account", bank_account_id)
        if not iban:
            raise ValidationError("iban required")
        acct["iban"] = iban.replace(" ", "").upper()
        acct["updated_at"] = _now()
        return self.store.pay_bank_accounts.save(bank_account_id, acct)

    def set_swift(self, *, bank_id: str, swift: str) -> dict[str, Any]:
        bank = self.store.pay_banks.get(bank_id)
        if bank is None:
            raise NotFoundError("bank", bank_id)
        if not swift:
            raise ValidationError("swift required")
        bank["swift"] = swift.upper()
        bank["updated_at"] = _now()
        return self.store.pay_banks.save(bank_id, bank)

    def verify_account(self, *, bank_account_id: str, method: str = "micro_deposit") -> dict[str, Any]:
        acct = self.store.pay_bank_accounts.get(bank_account_id)
        if acct is None:
            raise NotFoundError("bank_account", bank_account_id)
        vid = _id("pay_ver")
        acct["verified"] = True
        acct["verified_at"] = _now()
        self.store.pay_bank_accounts.save(bank_account_id, acct)
        return self.store.pay_verifications.save(
            vid,
            {
                "verification_id": vid,
                "bank_account_id": bank_account_id,
                "method": method,
                "status": "verified",
                "at": _now(),
            },
        )

    def import_statement(
        self, *, bank_account_id: str, period: str, lines: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        if self.store.pay_bank_accounts.get(bank_account_id) is None:
            raise NotFoundError("bank_account", bank_account_id)
        if not period:
            raise ValidationError("period required")
        sid = _id("pay_stmt")
        entries = lines or [{"memo": "Opening balance", "amount": 0.0}]
        return self.store.pay_statements.save(
            sid,
            {
                "statement_id": sid,
                "bank_account_id": bank_account_id,
                "period": period,
                "lines": entries,
                "line_count": len(entries),
                "imported_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "banks": self.store.pay_banks.count(),
            "bank_accounts": self.store.pay_bank_accounts.count(),
            "verifications": self.store.pay_verifications.count(),
            "statements": self.store.pay_statements.count(),
        }
