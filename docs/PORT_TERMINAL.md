# Port ERP Terminal Operations — Sprint 9.3

Terminal, warehouse, yard, gate, equipment, and planning for **Port ERP 1.2.0-alpha**.

| Field | Value |
|-------|-------|
| Application version | `1.2.0-alpha` |
| Terminal engine | `1.0` |
| Platform | AI Platform Core v3 (bridge only) |
| Ecosystem | AI Ecosystem v1.5 (bridge only) |

**Hard constraint:** Platform Core and Ecosystem are not modified. Everything lives under `applications/port_erp/`.

## Engines

| Engine | Module |
|--------|--------|
| Terminal Operations Engine | `terminal_operations/engine.py` |
| Yard Management Engine | `yard_management/engine.py` |
| Warehouse Engine | `warehouse_management/engine.py` |
| Gate Control Engine | `gate_management/engine.py` |
| Crane Scheduling Engine | `cranes/engine.py` |
| Equipment Manager | `equipment/engine.py` |
| Storage Optimizer | `storage/engine.py` |
| Dispatch Engine | `dispatch/engine.py` |
| Planning Engine | `planning/engine.py` |
| Inventory Service | `inventory/service.py` |

## Warehouse

Receiving · Storage · Picking · Packing · Cross Dock · Inventory · Stock Movements · Cycle Count · Zone Management

## Container Yard

Yard Blocks · Rows · Slots · Automatic Slot Assignment · Container Relocation · Stack Planning · Density Optimization

## Gate Operations

Truck Check-in / Check-out · Appointments · Vehicle Queue · OCR abstraction · QR abstraction · Driver verification · Access permissions

## Terminal Planning

Berth · Crane · Labor · Equipment · Yard · Warehouse planning

## Equipment

STS Cranes · RTG · RMG · Reach Stackers · Forklifts · Terminal Trucks · Trailers · Maintenance Schedule

## Events

`TruckArrived` · `TruckDeparted` · `ContainerStored` · `ContainerMoved` · `ContainerReleased` · `CraneAssigned` · `CraneFinished` · `WarehouseUpdated` · `GateApproved` · `GateRejected`

## REST API

| Area | Prefix |
|------|--------|
| Terminal | `/api/port/v1/terminal` |
| Warehouse | `/api/port/v1/warehouse` |
| Yard | `/api/port/v1/yard` |
| Gate | `/api/port/v1/gate` |
| Equipment | `/api/port/v1/equipment` |
| Planning | `/api/port/v1/planning` |

### Key endpoints

```
GET  /api/port/v1/terminal
POST /api/port/v1/yard/blocks
POST /api/port/v1/yard/assign
POST /api/port/v1/warehouse
POST /api/port/v1/warehouse/inventory
POST /api/port/v1/gate/check-in
POST /api/port/v1/gate/visits/{id}/approve
POST /api/port/v1/equipment
POST /api/port/v1/equipment/cranes/assign
POST /api/port/v1/planning
```

## Developer guide

```python
from applications.port_erp import port_erp
from applications.port_erp.shared.models import Gate
from applications.port_erp.terminal_operations.models import YardBlock, Equipment, EquipmentType

block = port_erp.terminal.yard.create_block(
    YardBlock(terminal_id="t1", name="A", rows=2, slots_per_row=3)
)
slot = await port_erp.terminal.yard.assign_slot("container-1", terminal_id="t1")
crane = port_erp.terminal.equipment.register(
    Equipment(name="STS-1", equipment_type=EquipmentType.STS, terminal_id="t1")
)
```

## Related

- [PORT_ERP.md](PORT_ERP.md)
- [PORT_TRACKING.md](PORT_TRACKING.md)
