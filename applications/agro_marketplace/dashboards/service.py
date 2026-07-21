# Role-based dashboards for Agro Marketplace BI.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.analytics.events import DashboardUpdatedEvent
from applications.agro_marketplace.analytics.models import DashboardKind, DashboardSnapshot
from applications.agro_marketplace.analytics.service import AnalyticsService, analytics_service
from applications.agro_marketplace.insights.service import InsightsService, insights_service
from applications.agro_marketplace.kpi.service import KPIService, kpi_service
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class DashboardsService:
    def __init__(
        self,
        store: AgroStore | None = None,
        analytics: AnalyticsService | None = None,
        kpi: KPIService | None = None,
        insights: InsightsService | None = None,
    ) -> None:
        self._store = store or agro_store
        self._analytics = analytics or analytics_service
        self._kpi = kpi or kpi_service
        self._insights = insights or insights_service

    async def _publish(self, snap: DashboardSnapshot) -> DashboardSnapshot:
        saved = self._store.dashboard_snapshots.save(snap.snapshot_id, snap)
        await publish(
            DashboardUpdatedEvent(dashboard_kind=saved.kind.value, snapshot_id=saved.snapshot_id)
        )
        return saved

    async def build(self, kind: DashboardKind, *, subject_id: str = "") -> DashboardSnapshot:
        builders = {
            DashboardKind.EXECUTIVE: self.executive,
            DashboardKind.FARMER: self.farmer,
            DashboardKind.BUYER: self.buyer,
            DashboardKind.SUPPLIER: self.supplier,
            DashboardKind.EXPORTER: self.exporter,
            DashboardKind.WAREHOUSE: self.warehouse,
            DashboardKind.LOGISTICS: self.logistics,
            DashboardKind.MARKETPLACE: self.marketplace,
        }
        return await builders[kind](subject_id=subject_id)

    async def executive(self, *, subject_id: str = "") -> DashboardSnapshot:
        kpis = await self._kpi.calculate_all()
        metrics = self._analytics.dashboard_metrics()
        export = self._analytics.export_analytics()
        insights = await self._insights.generate(metrics={s.name.value: s.value for s in kpis})
        snap = DashboardSnapshot(
            kind=DashboardKind.EXECUTIVE,
            title="Executive Dashboard",
            subject_id=subject_id,
            widgets=[
                {"type": "metrics", "data": metrics},
                {"type": "export", "data": export},
                {"type": "orders_by_status", "data": self._analytics.orders_by_status()},
            ],
            kpis=[k.to_dict() for k in kpis],
            insights=[i.to_dict() for i in insights[:5]],
        )
        return await self._publish(snap)

    async def farmer(self, *, subject_id: str = "") -> DashboardSnapshot:
        data = self._analytics.harvest_analytics()
        crop = self._analytics.crop_analytics()
        snap = DashboardSnapshot(
            kind=DashboardKind.FARMER,
            title="Farmer Dashboard",
            subject_id=subject_id,
            widgets=[
                {"type": "harvest", "data": data},
                {"type": "crops", "data": crop},
                {"type": "activity", "data": {"farmers": self._store.farmers.count()}},
            ],
        )
        return await self._publish(snap)

    async def buyer(self, *, subject_id: str = "") -> DashboardSnapshot:
        snap = DashboardSnapshot(
            kind=DashboardKind.BUYER,
            title="Buyer Dashboard",
            subject_id=subject_id,
            widgets=[
                {"type": "demand", "data": self._analytics.demand_analytics()},
                {"type": "pricing", "data": self._analytics.pricing_analytics()},
                {"type": "customers", "data": self._analytics.customer_analytics()},
            ],
        )
        return await self._publish(snap)

    async def supplier(self, *, subject_id: str = "") -> DashboardSnapshot:
        snap = DashboardSnapshot(
            kind=DashboardKind.SUPPLIER,
            title="Supplier Dashboard",
            subject_id=subject_id,
            widgets=[
                {"type": "supply", "data": self._analytics.supply_analytics()},
                {"type": "sales", "data": self._analytics.sales_analytics()},
            ],
        )
        return await self._publish(snap)

    async def exporter(self, *, subject_id: str = "") -> DashboardSnapshot:
        snap = DashboardSnapshot(
            kind=DashboardKind.EXPORTER,
            title="Exporter Dashboard",
            subject_id=subject_id,
            widgets=[
                {"type": "export", "data": self._analytics.export_analytics()},
                {"type": "regional", "data": self._analytics.regional_analytics()},
            ],
        )
        return await self._publish(snap)

    async def warehouse(self, *, subject_id: str = "") -> DashboardSnapshot:
        snap = DashboardSnapshot(
            kind=DashboardKind.WAREHOUSE,
            title="Warehouse Dashboard",
            subject_id=subject_id,
            widgets=[
                {"type": "inventory", "data": self._analytics.inventory_analytics()},
                {
                    "type": "capacity",
                    "data": {
                        "warehouses": self._store.agro_warehouses.count() or self._store.warehouses.count()
                    },
                },
            ],
        )
        return await self._publish(snap)

    async def logistics(self, *, subject_id: str = "") -> DashboardSnapshot:
        snap = DashboardSnapshot(
            kind=DashboardKind.LOGISTICS,
            title="Logistics Dashboard",
            subject_id=subject_id,
            widgets=[
                {
                    "type": "logistics",
                    "data": {
                        "deliveries": self._store.deliveries.count(),
                        "carriers": self._store.carriers.count(),
                        "routes": self._store.route_plans.count(),
                        "containers": self._store.containers.count(),
                    },
                },
                {"type": "export", "data": self._analytics.export_analytics()},
            ],
        )
        return await self._publish(snap)

    async def marketplace(self, *, subject_id: str = "") -> DashboardSnapshot:
        snap = DashboardSnapshot(
            kind=DashboardKind.MARKETPLACE,
            title="Marketplace Dashboard",
            subject_id=subject_id,
            widgets=[
                {"type": "sales", "data": self._analytics.sales_analytics()},
                {"type": "demand", "data": self._analytics.demand_analytics()},
                {"type": "supply", "data": self._analytics.supply_analytics()},
                {"type": "ai", "data": self._analytics.ai_insights()},
            ],
        )
        return await self._publish(snap)

    def list_snapshots(self, *, kind: DashboardKind | None = None) -> list[DashboardSnapshot]:
        items = self._store.dashboard_snapshots.list_all()
        if kind:
            items = [d for d in items if d.kind == kind]
        return sorted(items, key=lambda d: d.updated_at, reverse=True)


dashboards_service = DashboardsService()
