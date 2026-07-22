# Port ERP AI Operations & Digital Twin — Sprint 9.6

Digital twin, executive AI, and operations control center for **Port ERP 1.5.0-alpha**.

| Field | Value |
|-------|-------|
| Application version | `1.5.0-alpha` |
| AI operations engine | `1.0` |
| Platform | AI Platform Core v3 (bridge only) |
| Ecosystem | AI Ecosystem v1.5 (bridge only) |

**Hard constraint:** Platform Core and Ecosystem are not modified. Everything lives under `applications/port_erp/`.

## Engines

| Engine | Module |
|--------|--------|
| Digital Twin Engine | `digital_twin/engine.py` |
| Executive AI Engine | `executive_ai/engine.py` |
| Decision Support Engine | `executive_ai/engine.py` |
| Berth Planning Engine | `berth_scheduler/engine.py` |
| Yard Optimization Engine | `yard_optimizer/engine.py` |
| Port Resource Engine | `resource_manager/engine.py` |
| Simulation Engine | `simulation/engine.py` |
| Predictive Analytics Engine | `prediction/engine.py` |
| Executive Dashboard Engine | `dashboard/engine.py` |
| Operations Center Engine | `operations_center/engine.py` |
| Optimization Engine | `optimization/engine.py` |
| Alerts Engine | `alerts/engine.py` |

## Digital Twin

Real-time port state across ships, berths, warehouses, yards, equipment, containers, vehicles, rail, road, plus weather abstraction.

## AI Planning

Berth allocation · Queue / congestion prediction · Equipment / container / truck / rail / warehouse / resource balancing

## Simulation scenarios

Storm delays · Equipment failures · Traffic overload · Terminal shutdown · Berth unavailable · Container overflow · Peak season · Emergency response

## Executive Dashboard KPIs

Port utilization · Berth occupancy · Terminal load · Warehouse capacity · Container dwell · Turnaround · ETA accuracy · Revenue · Bottlenecks

## Alerts

Critical congestion · ETA violation · Equipment failure · Container delay · Customs delay · Weather warning · Safety event · Capacity threshold

## REST API

| Area | Prefix |
|------|--------|
| Digital Twin | `/api/port/v1/digital-twin` |
| Dashboard | `/api/port/v1/dashboard` |
| Operations Center | `/api/port/v1/operations/center` |
| Simulation | `/api/port/v1/simulation` |
| Optimization | `/api/port/v1/optimization` |
| Executive | `/api/port/v1/executive` |

## Developer guide

```python
from applications.port_erp import port_erp

snap = await port_erp.ai_ops.twin.snapshot()
briefing = await port_erp.ai_ops.executive.briefing()
run = await port_erp.ai_ops.simulation.run("peak_season")
plans = await port_erp.ai_ops.optimization.run_all()
```

## Related

- [PORT_ERP.md](PORT_ERP.md)
- [PORT_TRACKING.md](PORT_TRACKING.md)
- [PORT_TERMINAL.md](PORT_TERMINAL.md)
- [PORT_CUSTOMS.md](PORT_CUSTOMS.md)
- [PORT_LOGISTICS.md](PORT_LOGISTICS.md)
