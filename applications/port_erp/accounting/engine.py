# Accounting Engine — double-entry abstraction, AR/AP, journal.

from __future__ import annotations

from applications.port_erp.currencies.engine import CurrencyEngine, currency_engine
from applications.port_erp.finance.models import AccountEntryType, JournalEntry
from applications.port_erp.shared.exceptions import ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class AccountingEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        currencies: CurrencyEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._currencies = currencies or currency_engine

    def post(
        self,
        *,
        debit_account: str,
        credit_account: str,
        amount: float,
        currency: str = "USD",
        reference: str = "",
        description: str = "",
        company_id: str = "",
    ) -> list[JournalEntry]:
        if amount <= 0:
            raise ValidationError("amount must be positive")
        if not debit_account or not credit_account:
            raise ValidationError("debit_account and credit_account are required")
        debit = JournalEntry(
            account_code=debit_account,
            entry_type=AccountEntryType.DEBIT,
            amount=amount,
            currency=currency,
            reference=reference,
            description=description,
            company_id=company_id,
        )
        credit = JournalEntry(
            account_code=credit_account,
            entry_type=AccountEntryType.CREDIT,
            amount=amount,
            currency=currency,
            reference=reference,
            description=description,
            company_id=company_id,
        )
        self._store.journal_entries.save(debit.entry_id, debit)
        self._store.journal_entries.save(credit.entry_id, credit)
        return [debit, credit]

    def journal(self, *, company_id: str | None = None) -> list[JournalEntry]:
        items = self._store.journal_entries.list_all()
        if company_id:
            items = [e for e in items if e.company_id == company_id]
        return sorted(items, key=lambda e: e.created_at)

    def receivables(self) -> float:
        # AR from unpaid commercial invoices
        total = 0.0
        for inv in self._store.commercial_invoices.list_all():
            total += max(0.0, inv.total - inv.amount_paid)
        return round(total, 2)

    def payables(self) -> float:
        # AP approximated from unpaid expenses
        return round(sum(e.amount for e in self._store.expense_records.list_all()), 2)

    def convert(self, amount: float, *, from_currency: str, to_currency: str) -> float:
        return self._currencies.convert(
            amount, from_currency=from_currency, to_currency=to_currency
        )


accounting_engine = AccountingEngine()
