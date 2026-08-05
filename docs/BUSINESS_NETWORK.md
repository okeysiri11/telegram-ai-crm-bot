# Enterprise Business Network

**Sprint:** 29.0  
**Frontend:** `src/web/src/runtime/businessNetwork/`  
**Backend:** `applications/enterprise_hub/business_network/`  
**API:** `/api/enterprise-ebn/v1`  
**Version:** `29.0`

## Role

Business relationship layer of Enterprise City — **not** a social network.

Integrates with Enterprise Runtime · Workflow Runtime · Automation Engine · AI Studio · Shell · Desktop · City · Security · Notifications.

## Architecture

```
City / Shell / Desktop / AI Studio
              │
              ▼
    Business Network Engine
  Profiles · Relationships · Graph
  Comms · Documents · Permissions
              │
              ├─ EventBus business_network_update
              ├─ Command Runtime (ebn_open, ebn_create_partner)
              └─ REST /api/enterprise-ebn/v1
```

## Modules

| Module | Path |
|--------|------|
| Profiles | `businessProfileService.ts` |
| Relationships | `relationshipService.ts` |
| Graph | `businessGraphEngine.ts` |
| Communication | `communicationService.ts` |
| Documents | `documentLinkService.ts` |
| Permissions | `ebnPermissions.ts` |
| City bridge | `cityBusinessBridge.ts` + `cityEbnBridge.ts` |
| REST client | `businessNetworkApi.ts` |

## Related

- [`BUSINESS_NETWORK_API.md`](./BUSINESS_NETWORK_API.md)
- [`SPRINT_29_0_RESULT.md`](./SPRINT_29_0_RESULT.md)
- [`AUTOMATION_ENGINE.md`](./AUTOMATION_ENGINE.md)
- [`WORKFLOW_RUNTIME.md`](./WORKFLOW_RUNTIME.md)
