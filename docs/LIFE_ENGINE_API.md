# Life Engine API

**Sprint:** 29.2  
**Prefix:** `/api/enterprise-life/v1`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health |
| GET | `/city` | Full City runtime snapshot |
| GET | `/occupancy?buildingId=` | Building occupancy |
| GET | `/timeline?subjectKind=&subjectId=` | Unified / filtered timeline |
| GET | `/events` | Recent life events |
| GET | `/inventory` | Endpoints + stats |

In-process source of truth: `lifeEngine` / `lifeEngineApi` (falls back when HTTP unavailable).
