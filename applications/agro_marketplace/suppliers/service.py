# SupplierService — supplier management.

from __future__ import annotations

from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import Supplier
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class SupplierService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def list_suppliers(self) -> list[Supplier]:
        return self._store.suppliers.list_all()

    def get_supplier(self, supplier_id: str) -> Supplier:
        supplier = self._store.suppliers.get(supplier_id)
        if supplier is None:
            raise NotFoundError("Supplier", supplier_id)
        return supplier

    def create_supplier(self, supplier: Supplier) -> Supplier:
        if not supplier.name:
            raise ValidationError("name is required")
        return self._store.suppliers.save(supplier.supplier_id, supplier)


supplier_service = SupplierService()
