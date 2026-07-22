# Parts Marketplace — OEM / aftermarket / used, VIN compatibility, price compare.

from __future__ import annotations

from applications.auto_marketplace.service_centers.models import Part, PartKind
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class PartsMarketplaceEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def add_part(self, part: Part) -> Part:
        if not part.sku or not part.name:
            raise ValidationError("sku and name are required")
        return self._store.parts_catalog.save(part.part_id, part)

    def get(self, part_id: str) -> Part:
        part = self._store.parts_catalog.get(part_id)
        if part is None:
            raise NotFoundError("Part", part_id)
        return part

    def list_parts(self, *, kind: str = "", supplier_id: str = "") -> list[Part]:
        items = self._store.parts_catalog.list_all()
        if kind:
            items = [p for p in items if p.kind.value == kind]
        if supplier_id:
            items = [p for p in items if p.supplier_id == supplier_id]
        return items

    def availability(self, part_id: str) -> dict:
        stocks = [s for s in self._store.parts_stock.list_all() if s.part_id == part_id]
        available = sum(max(0, s.quantity - s.reserved) for s in stocks)
        return {"part_id": part_id, "available": available, "warehouses": len(stocks)}

    def compare_prices(self, name_query: str) -> list[dict]:
        q = (name_query or "").lower()
        items = [p for p in self._store.parts_catalog.list_all() if q in p.name.lower() or q in p.sku.lower()]
        return sorted([p.to_dict() for p in items], key=lambda x: x["price"])

    def compatible_by_vin(self, vin: str) -> list[Part]:
        vin = (vin or "").strip().upper()
        if len(vin) < 8:
            raise ValidationError("vin must be at least 8 characters")
        make_hint = vin[0]  # coarse demo mapping
        out = []
        for part in self._store.parts_catalog.list_all():
            if vin in [v.upper() for v in part.compatible_vins]:
                out.append(part)
            elif part.compatible_makes and any(make_hint in m.upper()[:1] for m in part.compatible_makes):
                out.append(part)
            elif not part.compatible_vins and not part.compatible_makes:
                out.append(part)
        return out

    def metrics(self) -> dict:
        kinds = {k.value: 0 for k in PartKind}
        for p in self._store.parts_catalog.list_all():
            kinds[p.kind.value] = kinds.get(p.kind.value, 0) + 1
        return {"parts": self._store.parts_catalog.count(), "by_kind": kinds}


parts_marketplace_engine = PartsMarketplaceEngine()
