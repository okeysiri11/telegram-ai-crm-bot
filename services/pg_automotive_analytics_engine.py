# Automotive Analytics Engine v1 — inventory, sales, profitability, supplier analytics.

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from config import OWNER_ID
from database.models.automotive_analytics import AgingBucket
from database.models.automotive_inventory import VehicleStatus
from database.models.automotive_sales import SalesPipelineStage
from database.session import get_session
from repositories.automotive_analytics_repository import (
    InventoryMetricsRepository,
    ProfitabilityMetricsRepository,
    SalesMetricsRepository,
)
from repositories.automotive_cost_repository import VehicleCostRepository
from repositories.automotive_inventory_repository import VehicleRepository
from repositories.automotive_procurement_repository import (
    PurchaseOrderRepository,
    SupplierOfferRepository,
)
from repositories.automotive_sales_repository import LeadRepository
from repositories.automotive_warehouse_repository import (
    PartRepository,
    SupplierRepository,
)
from repositories.user_role_repository import UserRoleRepository

ANALYTICS_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MONEY = Decimal("0.01")
PCT = Decimal("0.0001")
IN_STOCK_STATUSES = frozenset({
    VehicleStatus.IN_STOCK.value,
    VehicleStatus.RESERVED.value,
})
SOLD_STATUSES = frozenset({
    VehicleStatus.SOLD.value,
    VehicleStatus.DELIVERED.value,
})


class AutomotiveAnalyticsEngineError(Exception):
    pass


class AutomotiveAnalyticsEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in ANALYTICS_ROLES for role in roles)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _pct(value: Decimal) -> Decimal:
        return value.quantize(PCT, rounding=ROUND_HALF_UP)

    @staticmethod
    def _aging_bucket(days: int) -> str:
        if days <= 30:
            return AgingBucket.DAYS_0_30.value
        if days <= 60:
            return AgingBucket.DAYS_31_60.value
        if days <= 90:
            return AgingBucket.DAYS_61_90.value
        return AgingBucket.DAYS_90_PLUS.value

    @staticmethod
    def _inventory_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "vehicle_id": str(row.vehicle_id) if row.vehicle_id else None,
            "metric_date": row.metric_date.isoformat(),
            "days_in_inventory": row.days_in_inventory,
            "aging_bucket": row.aging_bucket,
            "vehicle_status": row.vehicle_status,
            "inventory_value": (
                str(row.inventory_value) if row.inventory_value is not None else None
            ),
            "in_stock_count": row.in_stock_count,
            "sold_count": row.sold_count,
            "turnover_rate": (
                str(row.turnover_rate) if row.turnover_rate is not None else None
            ),
            "currency": row.currency,
        }

    @staticmethod
    def _sales_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "metric_date": row.metric_date.isoformat(),
            "total_leads": row.total_leads,
            "new_leads": row.new_leads,
            "contacted_count": row.contacted_count,
            "test_drive_count": row.test_drive_count,
            "negotiation_count": row.negotiation_count,
            "reserved_count": row.reserved_count,
            "contract_signed_count": row.contract_signed_count,
            "paid_count": row.paid_count,
            "delivered_count": row.delivered_count,
            "conversion_rate": str(row.conversion_rate),
            "total_pipeline_budget": (
                str(row.total_pipeline_budget)
                if row.total_pipeline_budget is not None
                else None
            ),
            "currency": row.currency,
        }

    @staticmethod
    def _profitability_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "vehicle_id": str(row.vehicle_id),
            "metric_date": row.metric_date.isoformat(),
            "total_cost": str(row.total_cost),
            "sale_price": str(row.sale_price) if row.sale_price else None,
            "target_price": str(row.target_price) if row.target_price else None,
            "margin_amount": str(row.margin_amount),
            "margin_percent": str(row.margin_percent),
            "roi_percent": str(row.roi_percent),
            "currency": row.currency,
        }

    @staticmethod
    async def compute_inventory_metrics(
        actor_id: int,
        *,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveAnalyticsEngineV1.user_can_access(actor_id):
            raise AutomotiveAnalyticsEngineError("Access denied")

        target_date = metric_date or datetime.now(timezone.utc).date()
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            vehicles = await VehicleRepository(session).list_all(limit=10000)
            repo = InventoryMetricsRepository(session)
            await repo.clear_for_date(target_date)

            in_stock_count = 0
            sold_count = 0
            total_inventory_value = Decimal("0")
            vehicle_rows: list[dict[str, Any]] = []

            for vehicle in vehicles:
                days = max(0, (now - vehicle.created_at).days)
                value = vehicle.purchase_price or vehicle.target_price or Decimal("0")

                if vehicle.status in IN_STOCK_STATUSES:
                    in_stock_count += 1
                    total_inventory_value += value
                    bucket = AutomotiveAnalyticsEngineV1._aging_bucket(days)
                    row = await repo.save(
                        metric_date=target_date,
                        vehicle_id=vehicle.id,
                        days_in_inventory=days,
                        aging_bucket=bucket,
                        vehicle_status=vehicle.status,
                        inventory_value=AutomotiveAnalyticsEngineV1._quantize(value),
                        currency=vehicle.currency,
                    )
                    vehicle_rows.append(
                        AutomotiveAnalyticsEngineV1._inventory_snapshot(row)
                    )
                elif vehicle.status in SOLD_STATUSES:
                    sold_count += 1

            avg_inventory = (
                total_inventory_value / in_stock_count
                if in_stock_count > 0
                else Decimal("0")
            )
            turnover = (
                AutomotiveAnalyticsEngineV1._pct(
                    Decimal(sold_count) / Decimal(max(in_stock_count, 1))
                )
                if in_stock_count or sold_count
                else Decimal("0")
            )

            fleet_row = await repo.save(
                metric_date=target_date,
                vehicle_id=None,
                in_stock_count=in_stock_count,
                sold_count=sold_count,
                inventory_value=AutomotiveAnalyticsEngineV1._quantize(total_inventory_value),
                turnover_rate=turnover,
                currency="USD",
                notes=f"avg_inventory_value={avg_inventory}",
            )

            aging_summary = {
                bucket.value: sum(
                    1 for r in vehicle_rows if r["aging_bucket"] == bucket.value
                )
                for bucket in AgingBucket
            }

            return {
                "fleet": AutomotiveAnalyticsEngineV1._inventory_snapshot(fleet_row),
                "vehicles": vehicle_rows,
                "aging_summary": aging_summary,
            }

    @staticmethod
    async def compute_sales_metrics(
        actor_id: int,
        *,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveAnalyticsEngineV1.user_can_access(actor_id):
            raise AutomotiveAnalyticsEngineError("Access denied")

        target_date = metric_date or datetime.now(timezone.utc).date()

        stage_map = {
            SalesPipelineStage.NEW_LEAD.value: "new_leads",
            SalesPipelineStage.CONTACTED.value: "contacted_count",
            SalesPipelineStage.TEST_DRIVE.value: "test_drive_count",
            SalesPipelineStage.NEGOTIATION.value: "negotiation_count",
            SalesPipelineStage.RESERVED.value: "reserved_count",
            SalesPipelineStage.CONTRACT_SIGNED.value: "contract_signed_count",
            SalesPipelineStage.PAID.value: "paid_count",
            SalesPipelineStage.DELIVERED.value: "delivered_count",
        }

        async with get_session() as session:
            leads = await LeadRepository(session).list_all(limit=10000)
            counts = {field: 0 for field in stage_map.values()}
            total_budget = Decimal("0")

            for lead in leads:
                field = stage_map.get(lead.pipeline_stage)
                if field:
                    counts[field] += 1
                if lead.budget:
                    total_budget += lead.budget

            total_leads = len(leads)
            delivered = counts["delivered_count"]
            conversion = (
                AutomotiveAnalyticsEngineV1._pct(Decimal(delivered) / Decimal(total_leads))
                if total_leads > 0
                else Decimal("0")
            )

            row = await SalesMetricsRepository(session).replace_for_date(
                target_date,
                total_leads=total_leads,
                conversion_rate=conversion,
                total_pipeline_budget=AutomotiveAnalyticsEngineV1._quantize(total_budget),
                **counts,
            )
            return AutomotiveAnalyticsEngineV1._sales_snapshot(row)

    @staticmethod
    async def compute_profitability_metrics(
        actor_id: int,
        *,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveAnalyticsEngineV1.user_can_access(actor_id):
            raise AutomotiveAnalyticsEngineError("Access denied")

        target_date = metric_date or datetime.now(timezone.utc).date()

        async with get_session() as session:
            vehicles = await VehicleRepository(session).list_all(limit=10000)
            cost_repo = VehicleCostRepository(session)
            metrics_repo = ProfitabilityMetricsRepository(session)
            await metrics_repo.clear_for_date(target_date)

            rows: list[dict[str, Any]] = []
            for vehicle in vehicles:
                cost_sheet = await cost_repo.get_by_vehicle(vehicle.id)
                total_cost = (
                    cost_sheet.total_cost
                    if cost_sheet
                    else vehicle.purchase_price or Decimal("0")
                )
                if total_cost <= 0:
                    continue

                sale_price = vehicle.sale_price or vehicle.target_price
                if cost_sheet and cost_sheet.target_price > 0:
                    sale_price = sale_price or cost_sheet.target_price

                revenue = sale_price or total_cost
                margin_amount = AutomotiveAnalyticsEngineV1._quantize(
                    revenue - total_cost
                )
                margin_percent = AutomotiveAnalyticsEngineV1._pct(
                    (margin_amount / revenue * Decimal("100"))
                    if revenue > 0
                    else Decimal("0")
                )
                roi_percent = AutomotiveAnalyticsEngineV1._pct(
                    (margin_amount / total_cost * Decimal("100"))
                    if total_cost > 0
                    else Decimal("0")
                )

                row = await metrics_repo.save(
                    vehicle_id=vehicle.id,
                    metric_date=target_date,
                    total_cost=AutomotiveAnalyticsEngineV1._quantize(total_cost),
                    sale_price=(
                        AutomotiveAnalyticsEngineV1._quantize(sale_price)
                        if sale_price
                        else None
                    ),
                    target_price=(
                        AutomotiveAnalyticsEngineV1._quantize(vehicle.target_price)
                        if vehicle.target_price
                        else None
                    ),
                    margin_amount=margin_amount,
                    margin_percent=margin_percent,
                    roi_percent=roi_percent,
                    currency=vehicle.currency,
                )
                rows.append(AutomotiveAnalyticsEngineV1._profitability_snapshot(row))

            averages = await metrics_repo.get_fleet_averages(target_date)
            return {
                "vehicles": rows,
                "fleet_averages": {k: str(v) for k, v in averages.items()},
            }

    @staticmethod
    async def get_supplier_analytics(
        actor_id: int,
    ) -> dict[str, Any]:
        if not await AutomotiveAnalyticsEngineV1.user_can_access(actor_id):
            raise AutomotiveAnalyticsEngineError("Access denied")

        async with get_session() as session:
            warehouse_suppliers = await SupplierRepository(session).list_active(
                limit=1000
            )
            parts = await PartRepository(session).list_all(limit=10000)
            purchase_orders = await PurchaseOrderRepository(session).list_all(limit=1000)
            offers = await SupplierOfferRepository(session).list_pending(limit=1000)

            parts_by_supplier: dict[str, dict[str, Any]] = {}
            for part in parts:
                if part.supplier_id is None:
                    continue
                key = str(part.supplier_id)
                entry = parts_by_supplier.setdefault(
                    key,
                    {
                        "parts_count": 0,
                        "total_stock_value": Decimal("0"),
                        "low_stock_count": 0,
                    },
                )
                entry["parts_count"] += 1
                if part.unit_cost:
                    entry["total_stock_value"] += part.unit_cost * part.quantity_on_hand
                if part.quantity_on_hand <= part.min_stock_level:
                    entry["low_stock_count"] += 1

            supplier_rows = []
            for supplier in warehouse_suppliers:
                sid = str(supplier.id)
                stats = parts_by_supplier.get(sid, {})
                supplier_rows.append({
                    "supplier_id": sid,
                    "name": supplier.name,
                    "source": "WAREHOUSE",
                    "parts_count": stats.get("parts_count", 0),
                    "total_stock_value": str(
                        AutomotiveAnalyticsEngineV1._quantize(
                            stats.get("total_stock_value", Decimal("0"))
                        )
                    ),
                    "low_stock_count": stats.get("low_stock_count", 0),
                })

            procurement_by_source: dict[str, int] = {}
            for po in purchase_orders:
                procurement_by_source[po.source] = (
                    procurement_by_source.get(po.source, 0) + 1
                )

            procurement_summary = {
                "total_purchase_orders": len(purchase_orders),
                "approved_orders": sum(
                    1 for po in purchase_orders if po.status == "APPROVED"
                ),
                "pending_offers": len(offers),
                "orders_by_source": procurement_by_source,
            }

            return {
                "warehouse_suppliers": supplier_rows,
                "procurement": procurement_summary,
            }

    @staticmethod
    async def refresh_all_metrics(
        actor_id: int,
        *,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveAnalyticsEngineV1.user_can_access(actor_id):
            raise AutomotiveAnalyticsEngineError("Access denied")

        inventory = await AutomotiveAnalyticsEngineV1.compute_inventory_metrics(
            actor_id,
            metric_date=metric_date,
        )
        sales = await AutomotiveAnalyticsEngineV1.compute_sales_metrics(
            actor_id,
            metric_date=metric_date,
        )
        profitability = (
            await AutomotiveAnalyticsEngineV1.compute_profitability_metrics(
                actor_id,
                metric_date=metric_date,
            )
        )
        suppliers = await AutomotiveAnalyticsEngineV1.get_supplier_analytics(actor_id)

        return {
            "inventory": inventory,
            "sales": sales,
            "profitability": profitability,
            "suppliers": suppliers,
        }

    @staticmethod
    async def get_inventory_metrics(
        actor_id: int,
        *,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveAnalyticsEngineV1.user_can_access(actor_id):
            raise AutomotiveAnalyticsEngineError("Access denied")

        target_date = metric_date or datetime.now(timezone.utc).date()
        async with get_session() as session:
            repo = InventoryMetricsRepository(session)
            fleet = await repo.get_fleet_summary(target_date)
            if fleet is None:
                raise AutomotiveAnalyticsEngineError(
                    f"No inventory metrics for {target_date}"
                )
            rows = await repo.list_by_date(target_date)
            vehicle_rows = [
                AutomotiveAnalyticsEngineV1._inventory_snapshot(r)
                for r in rows
                if r.vehicle_id is not None
            ]
            aging_summary = {
                bucket.value: sum(
                    1 for r in vehicle_rows if r["aging_bucket"] == bucket.value
                )
                for bucket in AgingBucket
            }
            return {
                "fleet": AutomotiveAnalyticsEngineV1._inventory_snapshot(fleet),
                "vehicles": vehicle_rows,
                "aging_summary": aging_summary,
            }

    @staticmethod
    async def get_sales_metrics(
        actor_id: int,
        *,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveAnalyticsEngineV1.user_can_access(actor_id):
            raise AutomotiveAnalyticsEngineError("Access denied")

        target_date = metric_date or datetime.now(timezone.utc).date()
        async with get_session() as session:
            row = await SalesMetricsRepository(session).get_by_date(target_date)
            if row is None:
                raise AutomotiveAnalyticsEngineError(
                    f"No sales metrics for {target_date}"
                )
            return AutomotiveAnalyticsEngineV1._sales_snapshot(row)

    @staticmethod
    async def get_profitability_metrics(
        actor_id: int,
        *,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveAnalyticsEngineV1.user_can_access(actor_id):
            raise AutomotiveAnalyticsEngineError("Access denied")

        target_date = metric_date or datetime.now(timezone.utc).date()
        async with get_session() as session:
            repo = ProfitabilityMetricsRepository(session)
            rows = await repo.list_by_date(target_date)
            if not rows:
                raise AutomotiveAnalyticsEngineError(
                    f"No profitability metrics for {target_date}"
                )
            averages = await repo.get_fleet_averages(target_date)
            return {
                "vehicles": [
                    AutomotiveAnalyticsEngineV1._profitability_snapshot(r) for r in rows
                ],
                "fleet_averages": {k: str(v) for k, v in averages.items()},
            }

    @staticmethod
    async def get_margin_analytics(
        actor_id: int,
        *,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        data = await AutomotiveAnalyticsEngineV1.get_profitability_metrics(
            actor_id,
            metric_date=metric_date,
        )
        vehicles = data["vehicles"]
        margins = sorted(
            vehicles,
            key=lambda v: Decimal(v["margin_amount"]),
            reverse=True,
        )
        return {
            "fleet_averages": data["fleet_averages"],
            "top_margin_vehicles": margins[:10],
            "low_margin_vehicles": list(reversed(margins[-10:])),
        }
