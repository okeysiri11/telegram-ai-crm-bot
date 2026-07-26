# API Core Audit — Sprint 30.2

## Mount surface (`api/server.py`)

| Prefix family | Owner | Versioning | Notes |
|---------------|-------|------------|-------|
| `/health`, `/liveness`, `/readiness`, `/metrics` | Gateway | N/A | Ops |
| `/api/*` | Legacy CRM | Unversioned | Debt TD-06 |
| `/api/v1/*` | Public API | Frozen v1 | Keep |
| `/management/v1/*` | Management | Versioned | OpenAPI recording present |
| `/api/platform-builder/v1` | Platform Builder | v1 | Hub APIs + wizards |
| `/api/ecosystem/v1` | Root ecosystem | v1 | Workforce/gov/assistant |
| `/api/ai-ecosystem/v1` | App ecosystem | v1 alpha | Bridge facade |
| `/api/auto/v1` (+ many) | Auto marketplace | v1 | Broad sub-API set |
| `/api/agro/v1`, `/api/agro-enterprise/v1` (+…) | Agro | v1 | Dual apps |
| `/api/crypto-enterprise/v1` (+…) | Crypto | v1 | BidEx-related |
| `/api/legal-enterprise/v1` (+…) | Legal | v1 | |
| `/api/drone/v1` | Drone | v1 | |
| `/api/enterprise-hub/v1` (+ ~60) | Enterprise Hub | v1 | Facade density high |
| `/api/ai-os/v1` | AI OS (+ hub MAOS) | v1 | Shared prefix — document |

## Contracts & consistency

| Concern | Status | Gap |
|---------|--------|-----|
| Naming (`/api/<domain>/v1`) | Mostly consistent | Legacy CRM exception |
| Response models | Per-app | No single envelope |
| Request/DTO/schemas | Per-app | Shared schemas partial |
| Events | Present | Cross-app schema weak |
| Versioning policy | Documented (EAS) | Not enforced everywhere |
| OpenAPI readiness | Hub/management stronger | PB + many verticals weaker |
| SDK readiness | Partial | Needs generated clients |

## Platform Builder API pattern (reference)

Consistent wizard lifecycle used by hubs 28.x–30.2:

- `GET …/catalog`, `GET …/status`  
- Domain GETs (+ some POST actions)  
- `POST …/sessions` → `PATCH …/sessions/{id}` → `POST …/sessions/{id}/create`  

**Auth today:** headers only — extend with Identity Center tokens before production web.

## Recommendations (extension only)

1. Publish **API ownership registry** (prefix → app → OpenAPI path).  
2. Extend EAS OpenAPI coverage to Platform Builder.  
3. Mark legacy CRM routes deprecated in docs; keep serving.  
4. Document `/api/ai-os/v1` subpath split (kernel vs MAOS).  
5. Freeze public contracts before first industry web portal ship.  
