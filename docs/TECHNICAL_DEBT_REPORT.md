# Technical Debt Report — Sprint 30.2

**Scope:** Identify contradictions and debt. **Do not remove functionality.** Prefer documentation ownership, extension, and composition.

---

## Priority debt (P0–P2)

| ID | Area | Debt | Severity | Recommended action |
|----|------|------|----------|-------------------|
| TD-01 | Naming | Three “ecosystem” layers (`ecosystem/`, `applications/ecosystem/`, PB `business_ecosystem`) | P0 | Publish ownership map; keep all code; route by prefix |
| TD-02 | Naming | Mission Control / Executive Center / drone Mission overlap | P0 | Clarify scopes in docs; no merge of runtimes |
| TD-03 | Naming | Command Center (web global vs PB OS vs hub ECC) | P0 | Navigation labels distinguish surfaces |
| TD-04 | Naming | Digital Twin (PB visual vs hub EDT vs drone twin) | P1 | Namespace glossary |
| TD-05 | Naming | `recommendation_engine` in 6+ places | P1 | Alias map; no rewrite |
| TD-06 | API | Unversioned CRM `/api/*` beside frozen `/api/v1` | P1 | Deprecation schedule only |
| TD-07 | API | Shared `/api/ai-os/v1` (kernel + hub MAOS) | P1 | Document subpath ownership |
| TD-08 | Auth | PB middleware header-only (`X-Principal`, `X-Platform-Role`) | P0 | Extend with live identity — do not replace UI |
| TD-09 | Web | No industry vertical React apps | P0 | Extend web; reuse EDS + portals |
| TD-10 | Web | 8 frame-only PB builders | P2 | Fill frames via UBF — do not fork |
| TD-11 | Web | Duplicate LoginPage paths (`auth/pages` vs `src/pages`) | P2 | Prefer Identity Center page |
| TD-12 | Test | Near-zero Vitest for platform-builder pages | P1 | Add smoke tests incrementally |
| TD-13 | OpenAPI | Uneven published specs for PB/verticals | P1 | Extend EAS governance coverage |
| TD-14 | Runtime | Dual entry (bot + API) orchestration | P1 | Deploy docs / compose |
| TD-15 | Product | Cafe vertical = catalog only | P1 | First Cafe app sprint extends foundation |
| TD-16 | Product | Beauty = libraries + hub, no `applications/beauty_*` | P2 | Optional app facade sprint |

---

## Subsystem debt notes

### API Core
Inconsistent response envelopes across apps; strong patterns inside each vertical. SDK readiness uneven.

### Event Bus
Multiple event packages; schema registry not enforced globally.

### Router
Many `register.py` files — correct for modularity; debt is **discoverability**, not duplication of business logic.

### Workflow Engine
PB Workflow Intelligence is analysis-only (correct). Executable workflows live elsewhere — document boundary to avoid “second engine” rewrites.

### Knowledge Graph / Digital Twin / Mission Control / Workspace
Operational at PB + hub levels. Debt is synonym collision, not missing code.

### Caching / Notifications / Search
Claimed in catalogs (realtime, HA) often as **in-memory readiness flags**. Production needs real backends — extend, don’t replace engines.

### Shared models / interfaces
EntityStore pattern in PB is consistent. Cross-app DTOs not unified — OpenAPI standardization path already exists (`docs/ENTERPRISE_API_STANDARDIZATION.md`).

---

## Contradictions to resolve (docs only)

1. Catalogs claim “distributed cache / HA” while engines use process memory — label as **foundation readiness**, not production HA.  
2. Business Ecosystem says “nothing is copied” while vertical apps historically grew independently — future work **connects** via universal modules.  
3. Frame builders appear in navigation as operational destinations but are thin frames — mark UI status badges.

---

## Explicit non-actions

- Do **not** delete legacy CRM API  
- Do **not** merge vertical apps into one monolith  
- Do **not** replace God Mode / Mission Control / Twin engines  
- Do **not** rewrite Telegram handlers into web in this sprint  
