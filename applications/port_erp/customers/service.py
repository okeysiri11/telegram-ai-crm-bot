# Customer Registry service.

from __future__ import annotations

from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Customer
from applications.port_erp.shared.store import PortStore, port_store


class CustomerRegistry:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def register(self, customer: Customer) -> Customer:
        if not customer.name:
            raise ValidationError("name is required")
        return self._store.customers.save(customer.customer_id, customer)

    def get(self, customer_id: str) -> Customer:
        customer = self._store.customers.get(customer_id)
        if customer is None:
            raise NotFoundError("Customer", customer_id)
        return customer

    def list_customers(self) -> list[Customer]:
        return self._store.customers.list_all()


customer_registry = CustomerRegistry()
