# Customer Account Engine — credit limits and balances.

from __future__ import annotations

from applications.port_erp.customers.service import CustomerRegistry, customer_registry
from applications.port_erp.finance.models import CustomerAccount
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class CustomerAccountEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        customers: CustomerRegistry | None = None,
    ) -> None:
        self._store = store or port_store
        self._customers = customers or customer_registry

    def open_account(self, account: CustomerAccount) -> CustomerAccount:
        self._customers.get(account.customer_id)
        if account.credit_limit < 0:
            raise ValidationError("credit_limit must be non-negative")
        existing = next(
            (
                a
                for a in self._store.customer_accounts.list_all()
                if a.customer_id == account.customer_id
            ),
            None,
        )
        if existing:
            existing.credit_limit = account.credit_limit
            existing.currency = account.currency or existing.currency
            return self._store.customer_accounts.save(existing.account_id, existing)
        return self._store.customer_accounts.save(account.account_id, account)

    def get_by_customer(self, customer_id: str) -> CustomerAccount:
        account = next(
            (a for a in self._store.customer_accounts.list_all() if a.customer_id == customer_id),
            None,
        )
        if account is None:
            raise NotFoundError("CustomerAccount", customer_id)
        return account

    def list_accounts(self) -> list[CustomerAccount]:
        return self._store.customer_accounts.list_all()

    def apply_balance(self, customer_id: str, *, delta: float) -> CustomerAccount:
        account = self.get_by_customer(customer_id)
        account.balance = round(account.balance + delta, 2)
        return self._store.customer_accounts.save(account.account_id, account)


customer_account_engine = CustomerAccountEngine()
