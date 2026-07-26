# Routing Audit — Sprint 30.2

## Routing layers

| Layer | Mechanism | Status |
|-------|-----------|--------|
| HTTP API routing | `api/server.py` → per-app `register.py` | **OK** — modular |
| Internal routing | `/internal/platform-builder/v1` (config) | Present; low usage visibility |
| Workflow routing | Workflow Studio + hub workflow APIs + PB analysis | **Boundary needed** |
| AI routing | `services/ai_router.py`, OpenRouter, agent registries, PB AI hubs | **Fragmented but live** |
| Event routing | Hub event platform + `events/` | Partial |
| Navigation routing | `src/web` App.tsx + menuEngine + PB registry | **OK** with duplicate command centers |
| Permission routing | RBAC v2 + middleware + God Mode | Partial end-to-end |

## Duplicated / overlapping routers

| Topic | Locations | Action |
|-------|-----------|--------|
| Ecosystem | `/api/ecosystem/v1`, `/api/ai-ecosystem/v1`, PB business-ecosystem | Keep; document |
| Command center | Web `/command-center`, PB `/platform-builder/command-center`, hub ECC | Keep; rename nav labels |
| Workflow intelligence | PB, hub WFI, `platform_workflow_intelligence` | Keep analysis vs execution distinct |
| AI OS | App register + hub MAOS on same prefix | Document subpaths |
| Login | Two page modules | Prefer auth Identity Center |

## Unnecessary layers?

No evidence that an entire router layer can be removed without breaking mounts. “Unnecessary” risk is **cognitive**, not runtime. Prefer registry docs over deletion.

## Conflicting routes

| Conflict | Risk | Mitigation |
|----------|------|------------|
| `/api/ai-os/v1` dual owners | Handler ambiguity if path collide | Review path tables; add conflict test |
| Soft nav routes without React Route | Dead links | Align menu ↔ App.tsx |
| Frame builders look operational | User confusion | Status badges |

## Routing diagram

```mermaid
flowchart LR
  Client[Web / Bot / Partners] --> GW[api/server.py]
  GW --> PB[/api/platform-builder/v1]
  GW --> Hub[/api/enterprise-hub/v1…]
  GW --> Vert[auto agro legal crypto drone…]
  GW --> Eco[/api/ecosystem/v1]
  GW --> Uni[/api/ai-ecosystem/v1]
  PB --> Engines[PB engines]
  Hub --> Libs[platform_* facades]
```

## Validation checklist

- [x] PB hubs registered under one prefix  
- [x] Vertical apps retain dedicated prefixes  
- [ ] Automated route-conflict scanner in CI (recommended backlog)  
- [ ] Nav soft-routes reconciled with App.tsx  
