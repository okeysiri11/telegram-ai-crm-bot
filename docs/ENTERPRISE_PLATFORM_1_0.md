# Enterprise Platform Version 1.0 → v1.1

**Sprint (current):** 1.1.1  
**Platform Builder:** v1.67.0  
**Release status:** Enterprise Platform v1.1 General Availability  
**v1.0 RC baseline docs retained for history**  
**GA cert:** 2026-07-27 (EP-08) · **Audit corrections:** Sprint 1.1.1

## Purpose

Подготовка Enterprise Platform Version 1.0 к Production: аудит, стабилизация, полировка, документация.  
**Без новых Engine / Core / Runtime / AI systems / Dashboard.**

**EP-08:** Pilot / Commercial / GA readiness — [GA_READINESS_REPORT.md](./GA_READINESS_REPORT.md).  
**Sprint 1.1.1:** Grand Audit High Priority closures — [SPRINT_1_1_1_GA_AUDIT.md](./SPRINT_1_1_1_GA_AUDIT.md).

## Sprint 34.2 — UX Polish (no functional changes)
- Dashboard: executive-first widget set, AI Recommendations removed as primary surface (AI Concierge dock is the main assistant).
- Navigation: Platform Builder menu grouped; Preview & Frames collapsed by default; canonical routes for AI/Twin.
- First Entry: mandatory onboarding shortened; progress + estimated time.
- Frame Builders: preview-only UI (Preview · Coming soon · Open Workspace Version).
- Search & empty states: improved “no results” experiences (Control Tower search, command palette) and added polished empty states for CRM/Knowledge/Marketplace shells and AI Team Center.

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
- [x] GA certification pack (EP-08)  
- [ ] Staging smoke of Executive Demo (operator)  
- [ ] Env secrets review for target deploy  

## Known Limitations

См. [KNOWN_LIMITATIONS_1_0.md](./KNOWN_LIMITATIONS_1_0.md).

## Roadmap 2.0

См. [ROADMAP_2_0.md](./ROADMAP_2_0.md).

## Related docs

- [ENTERPRISE_PLATFORM_V1_GA.md](./ENTERPRISE_PLATFORM_V1_GA.md)  
- [GA_READINESS_REPORT.md](./GA_READINESS_REPORT.md)  
- [ARCHITECTURE_AUDIT_34_0.md](./ARCHITECTURE_AUDIT_34_0.md)  
- [EXECUTIVE_DEMO_34_0.md](./EXECUTIVE_DEMO_34_0.md)  
- [RELEASE_NOTES_34_0.md](./RELEASE_NOTES_34_0.md)  
