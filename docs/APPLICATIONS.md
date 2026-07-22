# Applications

Registered in the Unified AI Ecosystem Application Registry:

| Application | Surface | Modified by Sprint 12.0? |
|-------------|---------|--------------------------|
| CRM | `api/crm_api` + app CRM modules | No |
| Auto Marketplace | `/api/auto/v1` | No |
| Agro Marketplace | `/api/agro/v1` | No |
| Port ERP | `/api/port/v1` | No |
| Drone Platform | `/api/drone/v1` | No |
| Platform Core | dependency | No |
| Knowledge System | `knowledge/` | Docs only |
| AI Ecosystem v1.5 | `/api/ecosystem/v1` | No (bridged) |
| Unified AI Ecosystem | `/api/ai-ecosystem/v1` | **New** |

Bootstrap:

```bash
POST /api/ai-ecosystem/v1/bootstrap
GET  /api/ai-ecosystem/v1/registry
```
