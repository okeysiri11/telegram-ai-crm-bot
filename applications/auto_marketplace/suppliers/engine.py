# Parts suppliers catalog.

from __future__ import annotations

from applications.auto_marketplace.service_centers.models import Supplier
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class SupplierEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def register(self, supplier: Supplier) -> Supplier:
        if not supplier.name:
            raise ValidationError("name is required")
        return self._store.parts_suppliers.save(supplier.supplier_id, supplier)

    def get(self, supplier_id: str) -> Supplier:
        item = self._store.parts_suppliers.get(supplier_id)
        if item is None:
            raise NotFoundError("Supplier", supplier_id)
        return item

    def list_all(self) -> list[Supplier]:
        return self._store.parts_suppliers.list_all()

    def metrics(self) -> dict:
        return {"suppliers": self._store.parts_suppliers.count()}


supplier_engine = SupplierEngine()
