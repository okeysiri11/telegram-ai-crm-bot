# Enterprise Asset Runtime

**Sprint:** 29.3  
**Package:** `src/web/src/runtime/assetRuntime/`  
**API:** `/api/enterprise-assets/v1`  
**Version:** `29.3`

## Role

Managed assets across City — buildings, fleet, IT, IP, documents, AI models — with ownership, location, lifecycle, and City query APIs.

Integrates with Life Engine (vehicles), Digital Citizens (assignments), Business Network (company ownership), and City live status.

## Architecture

```
Citizens · EBN · Life Engine
         │
         ▼
   Asset Runtime
 Registry · Ownership · Location · Lifecycle
         │
 EventBus asset_runtime_update
         │
   City Asset Query API
```

## Related

- [`ASSET_RUNTIME_API.md`](./ASSET_RUNTIME_API.md)
- [`SPRINT_29_3_RESULT.md`](./SPRINT_29_3_RESULT.md)
- [`LIFE_ENGINE.md`](./LIFE_ENGINE.md)
