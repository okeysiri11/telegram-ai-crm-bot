# Auto Marketplace — Service Centers, Parts & Maintenance (Sprint 10.5)

Multi-branch service operations, parts marketplace, and vehicle maintenance for **Auto Marketplace 4.1.2-enterprise**.

| Field | Value |
|-------|-------|
| Application version | `4.1.2-enterprise` |
| `service_engine` | `1.0` |
| `parts_engine` | `1.0` |
| `maintenance_engine` | `1.0` |

**Hard constraint:** AI Platform Core, AI Ecosystem, Agro Marketplace, and Port ERP are not modified. All work lives under `applications/auto_marketplace/`.

## Domain facade

```python
from applications.auto_marketplace import auto_marketplace

assert auto_marketplace.config.service_engine == "1.0"
metrics = auto_marketplace.service.metrics()
```

## Service Centers & Repair Orders

Branches, mechanics, advisors, repair bays, queues, and digital work orders from acceptance to delivery.

```python
from applications.auto_marketplace.service_centers.models import ServiceCenter, RepairOrder

center = auto_marketplace.service.centers.create_center(ServiceCenter(name="Downtown Service", branch_code="DT-01"))
order = auto_marketplace.service.repair_orders.accept(
    RepairOrder(center_id=center.center_id, vehicle_id="v1", customer_id="c1")
)
auto_marketplace.service.repair_orders.inspect(order.order_id, [{"item": "brakes", "ok": False}])
auto_marketplace.service.repair_orders.estimate(order.order_id, 450)
auto_marketplace.service.repair_orders.approve(order.order_id)
```

## Maintenance

Scheduled and mileage/time-based plans, reminders, and fleet maintenance.

```python
from applications.auto_marketplace.service_centers.models import MaintenancePlan

plan = auto_marketplace.service.maintenance.create_plan(
    MaintenancePlan(vehicle_id="v1", interval_km=10000, interval_days=180)
)
auto_marketplace.service.maintenance.schedule(plan_id=plan.plan_id, current_mileage_km=40000)
auto_marketplace.service.maintenance.reminders(vehicle_id="v1")
```

## Appointments

Online booking, calendar, mechanic/bay allocation, rescheduling, and notifications (`/api/auto/v1/appointments`).

## Parts Marketplace & Inventory

OEM / aftermarket / used parts, supplier catalog, VIN compatibility, warehouses, stock movements, POs, reservations, and low-stock alerts.

```python
from applications.auto_marketplace.service_centers.models import Part, PartKind, PartsWarehouse, StockItem

part = auto_marketplace.service.parts.add_part(Part(sku="BRK-01", name="Brake pad", kind=PartKind.OEM, price=89))
wh = auto_marketplace.service.inventory.create_warehouse(PartsWarehouse(name="Main", center_id="c1"))
auto_marketplace.service.inventory.upsert_stock(StockItem(warehouse_id=wh.warehouse_id, part_id=part.part_id, quantity=20))
```

## Warranty & Diagnostics

Manufacturer/extended warranty validation and claims; OBD/inspection/damage reports with AI diagnostics bridge.

## Service History

Unified maintenance, repair, parts, invoice, and warranty timeline per vehicle.

## REST API

| Prefix | Capability |
|--------|------------|
| `/api/auto/v1/service` | Centers, repair orders, diagnostics, history |
| `/api/auto/v1/maintenance` | Plans, schedules, reminders |
| `/api/auto/v1/parts` | Parts marketplace & suppliers |
| `/api/auto/v1/inventory` | Parts stock (+ legacy vehicle inventory routes) |
| `/api/auto/v1/appointments` | Service booking |
| `/api/auto/v1/warranty` | Policies & claims |

## Modules

`service_centers/` · `repair_orders/` · `maintenance/` · `appointments/` · `parts/` · `inventory/` · `suppliers/` · `warranty/` · `diagnostics/` · `service_history/`
