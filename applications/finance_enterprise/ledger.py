"""General Ledger — chart of accounts, journal entries, posting, balances."""

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


class GeneralLedger:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.account_types = list(DEFAULT_CONFIG.account_types)

    def add_account(
        self,
        *,
        code: str,
        name: str,
        account_type: str,
        parent_code: str = "",
        currency: str = "",
    ) -> dict[str, Any]:
        if not code or not name:
            raise ValidationError("account code and name required")
        at = account_type.lower().strip()
        if at not in self.account_types:
            raise ValidationError(f"account_type must be one of {self.account_types}")
        aid = _id("fe_coa")
        row = self.store.chart_of_accounts.save(
            aid,
            {
                "coa_id": aid,
                "code": code,
                "name": name,
                "account_type": at,
                "parent_code": parent_code,
                "currency": currency or DEFAULT_CONFIG.base_currency,
                "created_at": _now(),
            },
        )
        self.store.account_balances.save(
            code,
            {
                "account_code": code,
                "debit": 0.0,
                "credit": 0.0,
                "balance": 0.0,
                "currency": row["currency"],
                "updated_at": _now(),
            },
        )
        return row

    def create_journal_entry(
        self,
        *,
        description: str,
        lines: list[dict[str, Any]],
        reference: str = "",
        currency: str = "",
    ) -> dict[str, Any]:
        if not description:
            raise ValidationError("description required")
        if not lines or len(lines) < 2:
            raise ValidationError("at least two journal lines required")
        total_debit = 0.0
        total_credit = 0.0
        normalized: list[dict[str, Any]] = []
        for line in lines:
            account_code = str(line.get("account_code", "")).strip()
            if not account_code:
                raise ValidationError("line account_code required")
            debit = float(line.get("debit", 0) or 0)
            credit = float(line.get("credit", 0) or 0)
            if debit < 0 or credit < 0:
                raise ValidationError("debit/credit must be non-negative")
            if debit > 0 and credit > 0:
                raise ValidationError("line cannot have both debit and credit")
            if debit == 0 and credit == 0:
                raise ValidationError("line must have debit or credit")
            total_debit += debit
            total_credit += credit
            normalized.append(
                {
                    "account_code": account_code,
                    "debit": debit,
                    "credit": credit,
                    "memo": line.get("memo", ""),
                }
            )
        if round(total_debit, 6) != round(total_credit, 6):
            raise ValidationError("journal entry must balance (debits == credits)")
        jid = _id("fe_je")
        return self.store.journal_entries.save(
            jid,
            {
                "journal_id": jid,
                "description": description,
                "reference": reference,
                "currency": currency or DEFAULT_CONFIG.base_currency,
                "lines": normalized,
                "total_debit": total_debit,
                "total_credit": total_credit,
                "status": "draft",
                "created_at": _now(),
            },
        )

    def post(self, *, journal_id: str) -> dict[str, Any]:
        entry = self.store.journal_entries.get(journal_id)
        if entry is None:
            raise NotFoundError("journal_entry", journal_id)
        if entry.get("status") == "posted":
            raise ValidationError("journal entry already posted")
        postings = []
        for line in entry["lines"]:
            code = line["account_code"]
            bal = self.store.account_balances.get(code)
            if bal is None:
                raise ValidationError(f"unknown account_code in chart: {code}")
            bal["debit"] = float(bal["debit"]) + float(line["debit"])
            bal["credit"] = float(bal["credit"]) + float(line["credit"])
            bal["balance"] = float(bal["debit"]) - float(bal["credit"])
            bal["updated_at"] = _now()
            self.store.account_balances.save(code, bal)
            pid = _id("fe_post")
            postings.append(
                self.store.ledger_postings.save(
                    pid,
                    {
                        "posting_id": pid,
                        "journal_id": journal_id,
                        "account_code": code,
                        "debit": line["debit"],
                        "credit": line["credit"],
                        "posted_at": _now(),
                    },
                )
            )
        entry["status"] = "posted"
        entry["posted_at"] = _now()
        self.store.journal_entries.save(journal_id, entry)
        return {
            "journal_id": journal_id,
            "status": "posted",
            "postings": postings,
            "posting_count": len(postings),
        }

    def balance(self, *, account_code: str) -> dict[str, Any]:
        bal = self.store.account_balances.get(account_code)
        if bal is None:
            raise NotFoundError("account_balance", account_code)
        return bal

    def trial_balance(self) -> dict[str, Any]:
        rows = []
        total_debit = 0.0
        total_credit = 0.0
        for bal in self.store.account_balances.list_all():
            rows.append(
                {
                    "account_code": bal["account_code"],
                    "debit": bal["debit"],
                    "credit": bal["credit"],
                    "balance": bal["balance"],
                }
            )
            total_debit += float(bal["debit"])
            total_credit += float(bal["credit"])
        tid = _id("fe_tb")
        return self.store.trial_balances.save(
            tid,
            {
                "trial_balance_id": tid,
                "rows": rows,
                "total_debit": total_debit,
                "total_credit": total_credit,
                "balanced": round(total_debit, 6) == round(total_credit, 6),
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "accounts": self.store.chart_of_accounts.count(),
            "journal_entries": self.store.journal_entries.count(),
            "postings": self.store.ledger_postings.count(),
            "balances": self.store.account_balances.count(),
            "trial_balances": self.store.trial_balances.count(),
        }
