# Business Network API

**Sprint:** 29.0  
**Prefix:** `/api/enterprise-ebn/v1`  
**Versioning:** Enterprise `v1` — additive only, no breaking changes.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health + suite status |
| POST | `/bootstrap` | Seed foundation data |
| GET | `/inventory` | Profiles + relationships + endpoint list |
| GET | `/dashboard` | Stats + graph snapshot |
| GET | `/profiles` | List business profiles |
| GET | `/profiles/:id` | Profile detail |
| GET | `/relationships` | List relationships |
| POST | `/relationships` | Create pending relationship |
| POST | `/relationships/:id/approve` | Approve |
| POST | `/relationships/:id/reject` | Reject |
| GET | `/graph?profileId=` | Graph snapshot / connections |
| GET | `/city/:profileId` | City runtime facade |

## Local / demo

Vite plugin `vite.ebnApiPlugin.ts` serves the same prefix when Hub on `:8080` is absent (proxy bypass).

Frontend client `businessNetworkApi` falls back to in-process `businessNetworkEngine` when HTTP is unavailable.
