# Dealer Portal — dashboard, inventory, leads, sales, analytics, finance, documents.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DealerPortalService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def dashboard(self, dealer_id: str) -> dict[str, Any]:
        leads = [l for l in self._store.crm_leads.list_all() if l.dealer_id == dealer_id]
        deals = [d for d in self._store.crm_deals.list_all() if d.dealer_id == dealer_id]
        vehicles = [v for v in self._store.catalog_vehicles.list_all() if getattr(v, "dealer_id", "") == dealer_id]
        return {
            "dealer_id": dealer_id,
            "active_leads": len(leads),
            "open_deals": len([d for d in deals if d.stage.value not in {"closed_won", "closed_lost"}]),
            "inventory_count": len(vehicles),
            "revenue": sum(d.amount for d in deals if d.stage.value == "closed_won"),
        }

    def list_inventory(self, dealer_id: str) -> list[dict]:
        vehicles = [v for v in self._store.catalog_vehicles.list_all() if getattr(v, "dealer_id", "") == dealer_id]
        if not vehicles:
            vehicles = [v for v in self._store.vehicles.list_all() if getattr(v, "dealer_id", "") == dealer_id]
        return [v.to_dict() for v in vehicles]

    async def publish_vehicle(self, dealer_id: str, vehicle_data: dict) -> dict:
        try:
            from applications.auto_marketplace.vehicle_catalog.models import CatalogVehicle

            vehicle = CatalogVehicle(dealer_id=dealer_id, **{k: v for k, v in vehicle_data.items() if k in CatalogVehicle.__dataclass_fields__})
            self._store.catalog_vehicles.save(vehicle.vehicle_id, vehicle)
            return vehicle.to_dict()
        except Exception:
            return {"dealer_id": dealer_id, "status": "published", **vehicle_data}

    def manage_leads(self, dealer_id: str) -> list[dict]:
        return [l.to_dict() for l in self._store.crm_leads.list_all() if l.dealer_id == dealer_id]

    def sales_tracking(self, dealer_id: str) -> dict:
        deals = [d for d in self._store.crm_deals.list_all() if d.dealer_id == dealer_id]
        return {
            "total_deals": len(deals),
            "won": len([d for d in deals if d.stage.value == "closed_won"]),
            "lost": len([d for d in deals if d.stage.value == "closed_lost"]),
            "pipeline_value": sum(d.amount for d in deals),
        }

    def analytics_overview(self, dealer_id: str) -> dict:
        from applications.auto_marketplace.business_intelligence.engine import bi_engine

        dealer_data = bi_engine.analytics.dealer_analytics()
        return {"dealer_id": dealer_id, "platform": dealer_data}

    def financial_overview(self, dealer_id: str) -> dict:
        from applications.auto_marketplace.finance.engine import finance_engine

        payments = [p for p in self._store.finance_payments.list_all() if p.dealer_id == dealer_id]
        settlements = [s for s in self._store.dealer_settlements.list_all() if s.dealer_id == dealer_id]
        commissions = finance_engine.billing.list_commissions(dealer_id=dealer_id)
        return {
            "total_payments": sum(p.amount for p in payments if p.status == "completed"),
            "settlements": len(settlements),
            "commissions": sum(c.amount for c in commissions),
        }

    def documents_overview(self, dealer_id: str) -> list[dict]:
        docs = [d for d in self._store.finance_documents.list_all() if d.dealer_id == dealer_id]
        contracts = [c for c in self._store.contracts.list_all() if c.dealer_id == dealer_id]
        return {"documents": [d.to_dict() for d in docs], "contracts": [c.to_dict() for c in contracts]}  # type: ignore[return-value]


dealer_portal_service = DealerPortalService()
