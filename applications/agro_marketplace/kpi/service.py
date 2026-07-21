# KPI calculation engine for Agro Marketplace BI.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.analytics.events import KPICalculatedEvent
from applications.agro_marketplace.analytics.models import KPIName, KPISnapshot
from applications.agro_marketplace.shared.models import OrderStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class KPIService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def _save(self, snapshot: KPISnapshot) -> KPISnapshot:
        return self._store.kpi_snapshots.save(snapshot.snapshot_id, snapshot)

    async def calculate_all(self) -> list[KPISnapshot]:
        return [
            await self.calculate(KPIName.REVENUE),
            await self.calculate(KPIName.GROSS_MARGIN),
            await self.calculate(KPIName.ORDER_VOLUME),
            await self.calculate(KPIName.MARKETPLACE_GROWTH),
            await self.calculate(KPIName.EXPORT_VOLUME),
            await self.calculate(KPIName.INVENTORY_TURNOVER),
            await self.calculate(KPIName.WAREHOUSE_UTILIZATION),
            await self.calculate(KPIName.FARMER_ACTIVITY),
            await self.calculate(KPIName.BUYER_CONVERSION),
            await self.calculate(KPIName.AI_PERFORMANCE),
        ]

    async def calculate(self, name: KPIName) -> KPISnapshot:
        orders = [o for o in self._store.orders.list_all() if o.status != OrderStatus.CANCELLED]
        revenue = sum(o.total for o in orders)
        mp_orders = self._store.marketplace_orders.list_all()
        mp_revenue = sum(getattr(o, "total", 0) or getattr(o, "amount", 0) or 0 for o in mp_orders)
        total_revenue = revenue + mp_revenue

        if name == KPIName.REVENUE:
            snap = KPISnapshot(name=name, value=round(total_revenue, 2), unit="USD", target=100000)
        elif name == KPIName.GROSS_MARGIN:
            costs = total_revenue * 0.72
            margin = ((total_revenue - costs) / total_revenue) if total_revenue else 0.0
            snap = KPISnapshot(name=name, value=round(margin, 4), unit="ratio", target=0.25)
        elif name == KPIName.ORDER_VOLUME:
            snap = KPISnapshot(
                name=name,
                value=float(len(orders) + len(mp_orders)),
                unit="count",
                target=50,
            )
        elif name == KPIName.MARKETPLACE_GROWTH:
            offers = self._store.sales_offers.count()
            requests = self._store.purchase_requests.count()
            growth = float(offers + requests + self._store.agro_products.count())
            snap = KPISnapshot(name=name, value=growth, unit="index", target=100)
        elif name == KPIName.EXPORT_VOLUME:
            intl = self._store.intl_shipments.count()
            legacy = self._store.export_shipments.count()
            snap = KPISnapshot(name=name, value=float(intl + legacy), unit="shipments", target=20)
        elif name == KPIName.INVENTORY_TURNOVER:
            inventory = self._store.inventory_items.list_all()
            stock = sum(getattr(i, "available_quantity", 0) or getattr(i, "quantity", 0) or 0 for i in inventory)
            turnover = (total_revenue / stock) if stock else 0.0
            snap = KPISnapshot(name=name, value=round(turnover, 2), unit="ratio", target=2.0)
        elif name == KPIName.WAREHOUSE_UTILIZATION:
            warehouses = self._store.agro_warehouses.list_all() or self._store.warehouses.list_all()
            if warehouses:
                utils = []
                for w in warehouses:
                    cap = getattr(w, "capacity_tons", 0) or getattr(w, "capacity", 0) or 0
                    used = getattr(w, "used_tons", 0) or getattr(w, "used", 0) or 0
                    utils.append((used / cap) if cap else 0.0)
                util = sum(utils) / len(utils)
            else:
                util = 0.0
            snap = KPISnapshot(name=name, value=round(util, 4), unit="ratio", target=0.75)
        elif name == KPIName.FARMER_ACTIVITY:
            activity = float(
                self._store.farmers.count()
                + self._store.harvest_records.count()
                + self._store.sales_offers.count()
            )
            snap = KPISnapshot(name=name, value=activity, unit="index", target=40)
        elif name == KPIName.BUYER_CONVERSION:
            buyers = max(1, self._store.buyers.count())
            conversions = len(orders) + len(mp_orders)
            rate = conversions / buyers
            snap = KPISnapshot(name=name, value=round(rate, 4), unit="ratio", target=0.4)
        else:  # AI_PERFORMANCE
            invocations = self._store.agent_invocations.count()
            forecasts = self._store.forecasts.count()
            recs = self._store.recommendations.count()
            score = float(invocations + forecasts + recs)
            snap = KPISnapshot(name=name, value=score, unit="index", target=25)

        saved = self._save(snap)
        await publish(
            KPICalculatedEvent(snapshot_id=saved.snapshot_id, name=saved.name.value, value=saved.value)
        )
        return saved

    def list_snapshots(self, *, name: KPIName | None = None) -> list[KPISnapshot]:
        items = self._store.kpi_snapshots.list_all()
        if name:
            items = [s for s in items if s.name == name]
        return sorted(items, key=lambda s: s.calculated_at, reverse=True)

    def latest_map(self) -> dict[str, float]:
        latest: dict[str, KPISnapshot] = {}
        for snap in self.list_snapshots():
            if snap.name.value not in latest:
                latest[snap.name.value] = snap
        return {k: v.value for k, v in latest.items()}


kpi_service = KPIService()
