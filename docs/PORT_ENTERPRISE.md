# Port ERP — Enterprise Integration (Sprint 9.8)

Enterprise connectors for **Port ERP 2.0.0** (`enterprise_engine = 1.0`).

| Field | Value |
|-------|-------|
| Application version | `2.0.0` |
| Enterprise engine | `1.0` |
| API | `/api/port/v1/enterprise` · `/api/port/v1/integration` |

**Hard constraint:** Integration is bridge-only. Platform Core and Ecosystem packages are never modified.

## Connectors

| Target | Purpose |
|--------|---------|
| Agro Marketplace | Agricultural trade corridor |
| Auto Marketplace | Vehicle logistics corridor |
| CRM | Customer relationship |
| ERP | Enterprise resource planning |
| Warehouse | Inventory / WMS |
| Accounting | Ledger bridge |
| Finance | Commercial finance |
| AI Workforce | Platform workforce agents |
| Digital Twin | Port digital twin |
| Knowledge Graph | Platform knowledge |
| Identity | Ecosystem identity |
| Communication Bus | Ecosystem bus |

## Bootstrap

`POST /api/port/v1/enterprise/bootstrap` registers default connectors and marks them connected.

## Modules

`enterprise/` · `integration/`

```python
from applications.port_erp import port_erp

result = port_erp.enterprise.enterprise.bootstrap()
assert "agro_marketplace" in result["matrix"]
assert port_erp.config.enterprise_engine == "1.0"
```
