# API Ownership Registry — Sprint 30.3

Source of truth for HTTP prefixes mounted in `api/server.py`. **Extend OpenAPI coverage; do not renumber prefixes.**

| Prefix | Application / package | Public? | OpenAPI note |
|--------|----------------------|---------|--------------|
| `/health`, `/liveness`, `/readiness`, `/metrics` | Gateway | Ops | N/A |
| `/api/*` | Legacy CRM (`api/crm_api.py`) | Deprecated | See [CRM_API_DEPRECATION.md](./CRM_API_DEPRECATION.md) |
| `/api/v1/*` | Public API v1 | Yes | Frozen |
| `/management/v1/*` | Management | Internal | OpenAPI recording present |
| `/api/platform-builder/v1` | Platform Builder | Internal/builder | Extend EAS coverage |
| `/api/ecosystem/v1` | Root `ecosystem/` | Internal | |
| `/api/ai-ecosystem/v1` | `applications/ecosystem` | Internal | Alpha |
| `/api/auto/v1` (+ auto sub-APIs) | `auto_marketplace` | Partner/product | Strong |
| `/api/agro/v1` | `agro_marketplace` | Partner/product | |
| `/api/agro-enterprise/v1` (+…) | `agro_enterprise` | Product | |
| `/api/port/v1` | `port_erp` | Product | |
| `/api/port-enterprise/v1` (+…) | `port_enterprise` | Product | |
| `/api/drone/v1` | `drone_platform` | Product | |
| `/api/crypto-enterprise/v1` (+…) | `crypto_enterprise` | Product | |
| `/api/legal-enterprise/v1` (+…) | `legal_enterprise` | Product | |
| `/api/finance-enterprise/v1` (+…) | `finance_enterprise` | Product | |
| `/api/marketplace/v1` | `marketplace` | Product | |
| `/api/workflow-studio/v1` | `workflow_studio` | Builder | |
| `/api/executive/v1` | `executive_center` | Executive | Distinct from Mission Control |
| `/api/ai-os/v1` | `ai_os` + hub MAOS | Internal | Shared prefix — see glossary |
| `/api/enterprise/v1` | `enterprise` | Internal | |
| `/api/enterprise-hub/v1` (+ ~60) | `enterprise_hub` | Facades | EAS standardization home |

## Conflict watchlist

1. `/api/ai-os/v1` — dual registrars; enforce non-overlapping subpaths in CI later.  
2. Legacy `/api/*` vs `/api/v1/*` — migrate callers gradually.

## SDK readiness

| Surface | Status |
|---------|--------|
| Management | Best |
| Enterprise Hub EAS | Governance present |
| Platform Builder | Needs published OpenAPI |
| Vertical product APIs | Per-app; freeze before portal ship |
