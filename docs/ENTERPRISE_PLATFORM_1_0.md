# Enterprise Platform Version 1.0 — Release Candidate

**Sprint:** 34.0  
**Platform Builder:** v1.66.0  
**Release status:** Enterprise Platform v1.0 Release Candidate  
**Date:** 2026-07-26

## Purpose

Подготовка Enterprise Platform Version 1.0 к Production: аудит, стабилизация, полировка, документация.  
**Без новых Engine / Core / Runtime / AI систем / Dashboard.**

## Architecture Overview

Платформа — composition-first Enterprise Web поверх AI Platform Core:

```
Shell (FullLayout · Providers · RBAC · Notifications)
  ├── Mission Control / Control Tower / Dashboard
  ├── Enterprise Twin · City · Data Fabric · Integrations
  ├── AI Stack: Concierge · AI Team · Runtime · Autonomy · Governance
  ├── Intelligence: EI · Predictive · Learning · OKR
  ├── Workflow · Marketplace · AI Builder Studio
  └── Business Ecosystems (Beauty · Legal · Cafe · Agro · Auto · Drone · Bidex)
```

Все 33.x слои — **derive composition**, не новые Engine.

## Modules (v1.0 surface)

| Domain | Routes / hubs |
|--------|----------------|
| Executive | Control Tower, Mission Control, Dashboard, OKR, Governance |
| AI Ops | Concierge, AI Team, Runtime, Autonomy, Collaborative AI |
| Data | Data Fabric, Knowledge, Twin, Integrations |
| Intelligence | EI, Predictive, Learning |
| Build | AI Builder Studio, Workflow Center, Marketplace |
| Verticals | Beauty, Legal, Cafe, Agriculture, Automotive, Drone, Bidex |

## AI Stack

1. **Concierge** — единый оркестратор организации  
2. **AI Team** — specialists  
3. **AI Runtime** — очередь / orchestration view  
4. **Enterprise Intelligence** — priorities / cross-module  
5. **Predictive** — forecasts / what-if  
6. **Autonomy** — HITL approvals  
7. **Self-Learning** — continuous optimization recommendations  
8. **Governance** — policies / audit / AI control  

## Business Ecosystems

Industry extensions поверх platform core (не копируют core): Beauty, Legal, Cafe, Agriculture, Automotive, Drone, Bidex.

## Deployment Notes

- Web: `src/web` — `npm run build` → static `dist/`  
- API: Platform Builder + Enterprise Hub prefixes (`/api/platform-builder/v1`, hub modules)  
- Auth: existing production auth + RBAC (`PermissionGuard`, role catalog)  
- Offline: `OfflineBanner` in shell  
- Errors: root `ErrorBoundary` + recovery  
- Config: `applications/platform_builder/config.py` + `manifest.json` + `webConfig.ts`  

### Production checklist

- [x] Lint / Types (`tsc -b`)  
- [x] Unit / Vitest  
- [x] Production build  
- [x] Route map for Executive Demo  
- [x] Lazy-load heavy composition pages  
- [x] Collapsed platform strips (render budget)  
- [ ] Staging smoke of Executive Demo (operator)  
- [ ] Env secrets review for target deploy  

## Known Limitations

См. [KNOWN_LIMITATIONS_1_0.md](./KNOWN_LIMITATIONS_1_0.md).

## Roadmap 2.0

См. [ROADMAP_2_0.md](./ROADMAP_2_0.md).

## Related docs

- [ARCHITECTURE_AUDIT_34_0.md](./ARCHITECTURE_AUDIT_34_0.md)  
- [EXECUTIVE_DEMO_34_0.md](./EXECUTIVE_DEMO_34_0.md)  
- [RELEASE_NOTES_34_0.md](./RELEASE_NOTES_34_0.md)  
