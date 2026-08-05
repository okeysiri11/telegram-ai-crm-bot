# Enterprise Digital Citizens

**Sprint:** 29.1  
**Frontend:** `src/web/src/runtime/digitalCitizen/`  
**Backend:** `applications/enterprise_hub/digital_citizen/`  
**API:** `/api/enterprise-edc/v1`  
**Version:** `29.1`

## Role

Human layer of Enterprise Runtime / City. Companies are Business Network (29.0); people are Digital Citizens (29.1).

## Architecture

```
Shell / City / AI Studio / Desktop
              │
              ▼
     Digital Citizen Engine
  Profile · Membership · Workspace
  Presence · Personal AI · Activity
              │
   EventBus digital_citizen_update
   REST /api/enterprise-edc/v1
   EBN org ↔ businessProfileId
```

## Modules

| Concern | Module |
|---------|--------|
| Citizen profile | `citizenProfileService` |
| Org membership | `organizationMembershipService` |
| Workspace | `citizenWorkspaceService` |
| Personal AI | `personalAiRegistry` |
| Presence | `presenceEngine` |
| Activity | `activityEngine` / `citizenEvents` |
| Permissions | `citizenPermissions` |
| City facade | `cityCitizenBridge` |

## Related

- [`DIGITAL_CITIZEN_API.md`](./DIGITAL_CITIZEN_API.md)
- [`SPRINT_29_1_RESULT.md`](./SPRINT_29_1_RESULT.md)
- [`BUSINESS_NETWORK.md`](./BUSINESS_NETWORK.md)
