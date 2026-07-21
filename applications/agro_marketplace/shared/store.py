# In-memory entity store for Agro Marketplace.

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class EntityStore(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def reset(self) -> None:
        self._items.clear()

    def save(self, entity_id: str, entity: T) -> T:
        self._items[entity_id] = entity
        return entity

    def get(self, entity_id: str) -> T | None:
        return self._items.get(entity_id)

    def delete(self, entity_id: str) -> bool:
        return self._items.pop(entity_id, None) is not None

    def list_all(self) -> list[T]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)


class AgroStore:
    """Central in-memory persistence for Agro Marketplace."""

    def __init__(self) -> None:
        self.farmers: EntityStore = EntityStore()
        self.farms: EntityStore = EntityStore()
        self.fields: EntityStore = EntityStore()
        self.warehouses: EntityStore = EntityStore()
        self.suppliers: EntityStore = EntityStore()
        self.buyers: EntityStore = EntityStore()
        self.products: EntityStore = EntityStore()
        self.categories: EntityStore = EntityStore()
        self.crops: EntityStore = EntityStore()
        self.harvests: EntityStore = EntityStore()
        self.listings: EntityStore = EntityStore()
        self.offers: EntityStore = EntityStore()
        self.orders: EntityStore = EntityStore()
        self.contracts: EntityStore = EntityStore()
        self.deliveries: EntityStore = EntityStore()
        self.export_shipments: EntityStore = EntityStore()
        self.certificates: EntityStore = EntityStore()
        self.storage_lots: EntityStore = EntityStore()
        self.notifications: EntityStore = EntityStore()
        self.documents: EntityStore = EntityStore()
        self.payments: EntityStore = EntityStore()
        self.crm_leads: EntityStore = EntityStore()
        # Sprint 8.2 — catalog / warehouse / inventory
        self.agro_products: EntityStore = EntityStore()
        self.crop_records: EntityStore = EntityStore()
        self.crop_varieties: EntityStore = EntityStore()
        self.seasons: EntityStore = EntityStore()
        self.packaging: EntityStore = EntityStore()
        self.harvest_records: EntityStore = EntityStore()
        self.harvest_batches: EntityStore = EntityStore()
        self.agro_warehouses: EntityStore = EntityStore()
        self.storage_locations: EntityStore = EntityStore()
        self.storage_lot_records: EntityStore = EntityStore()
        self.inventory_items: EntityStore = EntityStore()
        self.inventory_movements: EntityStore = EntityStore()
        self.quality_certificates: EntityStore = EntityStore()
        self.lab_results: EntityStore = EntityStore()
        # Sprint 8.3 — CRM / trading / marketplace
        self.farmer_profiles: EntityStore = EntityStore()
        self.buyer_profiles: EntityStore = EntityStore()
        self.supplier_profiles: EntityStore = EntityStore()
        self.exporter_profiles: EntityStore = EntityStore()
        self.agro_leads: EntityStore = EntityStore()
        self.crm_contacts: EntityStore = EntityStore()
        self.crm_tasks: EntityStore = EntityStore()
        self.purchase_requests: EntityStore = EntityStore()
        self.sales_offers: EntityStore = EntityStore()
        self.price_requests: EntityStore = EntityStore()
        self.negotiations: EntityStore = EntityStore()
        self.delivery_agreements: EntityStore = EntityStore()
        self.marketplace_orders: EntityStore = EntityStore()
        self.trade_contracts: EntityStore = EntityStore()
        self.trading_sessions: EntityStore = EntityStore()
        self.marketplace_deals: EntityStore = EntityStore()
        self.exporters: EntityStore = EntityStore()
        # Sprint 8.4 — Agricultural AI
        self.agro_agents: EntityStore = EntityStore()
        self.agent_invocations: EntityStore = EntityStore()
        self.recommendations: EntityStore = EntityStore()
        self.forecasts: EntityStore = EntityStore()
        self.knowledge_articles: EntityStore = EntityStore()
        self.executive_reports: EntityStore = EntityStore()
        self.ai_workflow_tasks: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


agro_store = AgroStore()
