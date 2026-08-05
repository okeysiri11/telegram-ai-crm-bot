# Digital Citizen API

**Sprint:** 29.1  
**Prefix:** `/api/enterprise-edc/v1`

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health |
| POST | `/bootstrap` | Seed |
| GET | `/inventory` | Inventory |
| GET | `/dashboard` | Stats |
| GET | `/citizens` | List citizens |
| GET | `/citizens/:id` | Citizen detail |
| GET | `/memberships?citizenId=` | Memberships |
| GET | `/presence` | Presence snapshot |
| POST | `/presence` | Set presence `{ citizenId, status }` |
| GET | `/city/:citizenId` | City runtime facade |

Local Vite plugin `vite.edcApiPlugin.ts` serves the prefix when Hub is offline. Client `digitalCitizenApi` falls back to in-process engine.
