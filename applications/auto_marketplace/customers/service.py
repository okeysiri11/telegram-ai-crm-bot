# CustomerService — customer profile management.

from __future__ import annotations

from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.models import Customer
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CustomerService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def list_customers(self) -> list[Customer]:
        return self._store.customers.list_all()

    def get_customer(self, customer_id: str) -> Customer:
        customer = self._store.customers.get(customer_id)
        if customer is None:
            raise NotFoundError("Customer", customer_id)
        return customer

    def create_customer(self, customer: Customer) -> Customer:
        return self._store.customers.save(customer.customer_id, customer)

    def update_preferences(self, customer_id: str, preferences: dict) -> Customer:
        customer = self.get_customer(customer_id)
        customer.preferences.update(preferences)
        return self._store.customers.save(customer_id, customer)


customer_service = CustomerService()
