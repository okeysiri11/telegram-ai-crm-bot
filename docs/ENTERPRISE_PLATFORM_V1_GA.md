# Enterprise Platform v1.1 — General Availability

**Status:** General Availability (product certification)  
**Current patch:** Sprint **1.1.1** — [SPRINT_1_1_1_GA_AUDIT.md](./SPRINT_1_1_1_GA_AUDIT.md)  
**Date:** 2026-07-27  
**Platform Builder:** v1.67.0  
**Sprint label:** 1.1.1  
**Web:** design system 9.4.0 · webConfig sprint 1.1.1  
**Predecessor RC baseline:** [ENTERPRISE_PLATFORM_1_0.md](./ENTERPRISE_PLATFORM_1_0.md)  

---

## What GA means

Enterprise Platform v1.0 GA is the **same frozen architecture** as the Release Candidate, certified for:

1. External and internal **pilots**
2. **Commercial demos** and sales presentations
3. Daily executive use of the core path (Brief → City → Concierge → Control Tower)

**Not in GA scope:** new Engines, Runtime/AI Core/Data Fabric redesigns, or large feature packs (Roadmap 2.0).

---

## Product surface (GA)

```
Shell (FullLayout · Providers · RBAC · Offline · ErrorBoundary)
  ├── Morning Brief / Executive Dashboard
  ├── Enterprise City · Mission Control · Control Tower
  ├── AI Concierge (Advisor) · AI Team · Runtime · Autonomy · Governance
  ├── Decision Continue strip (cross-module handoff)
  ├── Twin · Data Fabric · Integrations · Intelligence · OKR
  ├── Builder Studio · Workflow · Marketplace
  └── Business Ecosystems (7) — Beauty · Legal · Cafe · Agro · Auto · Drone · Bidex
```

---

## Canonical customer journey

| Step | Route | Value |
|------|-------|--------|
| Demo | `/demo/scenario` | Timed commercial path |
| Login | `/login` | Enterprise identity |
| First Entry | `/onboarding/first-entry` | Role · company · ready |
| Morning Brief | `/dashboard?mode=executive` | Observation · Attention · Next |
| Dashboard | `/dashboard` | Decision Flow |
| Enterprise City | `/enterprise-city` | Company map at a glance |
| Mission Control | `/platform-builder/mission-control` | Live ops health |
| AI Concierge | `/platform-builder/concierge` | Advisor decisions |
| Control Tower | `/platform-builder/control-tower` | Owner decide-now |
| Settings | `/settings` | Preferences · profile |

---

## Experience baseline (EP-01…EP-07)

| Layer | Doc |
|-------|-----|
| Executive Experience | [EP_01_EXECUTIVE_EXPERIENCE.md](./EP_01_EXECUTIVE_EXPERIENCE.md) |
| Design Language | [EP_02_ENTERPRISE_DESIGN_LANGUAGE.md](./EP_02_ENTERPRISE_DESIGN_LANGUAGE.md) |
| Motion Language | [EP_03_MOTION_DESIGN_LANGUAGE.md](./EP_03_MOTION_DESIGN_LANGUAGE.md) |
| AI Personality | [EP_04_AI_PERSONALITY.md](./EP_04_AI_PERSONALITY.md) |
| City Experience | [EP_05_ENTERPRISE_CITY.md](./EP_05_ENTERPRISE_CITY.md) |
| Decision Flow | [EP_06_ENTERPRISE_INTELLIGENCE.md](./EP_06_ENTERPRISE_INTELLIGENCE.md) |
| Production Excellence | [EP_07_PRODUCTION_EXCELLENCE.md](./EP_07_PRODUCTION_EXCELLENCE.md) |

---

## Operating constraints

- Do **not** invent new Engine / Store / Runtime / AI Core / Data Fabric packages for polish work.
- Prefer composition, copy, CSS tokens, and existing shells.
- Known limitations remain documented in [KNOWN_LIMITATIONS_1_0.md](./KNOWN_LIMITATIONS_1_0.md).
- Roadmap 2.0: [ROADMAP_2_0.md](./ROADMAP_2_0.md).

---

## Certification artifacts

- [GA_READINESS_REPORT.md](./GA_READINESS_REPORT.md)
- [FINAL_EQI_REPORT.md](./FINAL_EQI_REPORT.md)
- [PILOT_CHECKLIST.md](./PILOT_CHECKLIST.md)
- [EXECUTIVE_DEMO_34_0.md](./EXECUTIVE_DEMO_34_0.md)

---

## Release note for clients

**Enterprise Platform v1.0 is General Availability.**  
Owners can onboard, see the company in seconds, follow Advisor recommendations, and decide in Control Tower — without architectural surprises between RC and GA.
