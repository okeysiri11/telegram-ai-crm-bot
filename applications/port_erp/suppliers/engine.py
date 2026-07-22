# Supplier registry for commercial payables.

from __future__ import annotations

from applications.port_erp.finance.models import Supplier
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class SupplierEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def register(self, supplier: Supplier) -> Supplier:
        if not supplier.name:
            raise ValidationError("name is required")
        return self._store.suppliers.save(supplier.supplier_id, supplier)

    def get(self, supplier_id: str) -> Supplier:
        item = self._store.suppliers.get(supplier_id)
        if item is None:
            raise NotFoundError("Supplier", supplier_id)
        return item

    def list_suppliers(self) -> list[Supplier]:
        return self._store.suppliers.list_all()


supplier_engine = SupplierEngine()
