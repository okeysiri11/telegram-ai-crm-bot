# Closed Beta

**Sprint:** 32.5 — Closed Beta Launch Preparation (extends 31.0 RC)  
**Version tag:** `32.5-closed-beta`

> **Naming:** Cafe Pilot Execution also uses Sprint **31.0**. Enterprise Intelligence uses Sprint **32.5**.  
> This document is the **Closed Beta** track. See [`CLOSED_BETA_GUIDE.md`](./CLOSED_BETA_GUIDE.md) for the launch guide.

## What ships

A coherent Enterprise Platform integrating Auth, First Run, role dashboards, CRM, Projects, Knowledge, Calendar, Notifications, Drive, Marketplace, AI Studio, Production Studio, City, Runtime, Security Center, Navigation, and Settings — Russian UI default.

## Surfaces

Canonical list: `src/web/src/closed-beta/closedBetaCatalog.ts` (`CLOSED_BETA_SURFACES`).

## Entry

1. Login (email or Google) → `/login`
2. Incomplete first-entry → `/onboarding/first-entry`
3. Role home (Owner `/owner`, Admin `/admin`, Manager `/dashboards/manager`, Employee `/dashboards/employee`, …)
4. Enterprise City → `/city` (buildings open real modules)

## Related

[CLOSED_BETA_GUIDE.md](./CLOSED_BETA_GUIDE.md) · [FIRST_USER_JOURNEY.md](./FIRST_USER_JOURNEY.md) · [FIRST_RUN.md](./FIRST_RUN.md) · [RELEASE_CHECKLIST.md](./RELEASE_CHECKLIST.md) · [KNOWN_LIMITATIONS.md](./KNOWN_LIMITATIONS.md) · [SPRINT_32_5_RESULT.md](./SPRINT_32_5_RESULT.md) · [DEPLOYMENT.md](./DEPLOYMENT.md) · [INSTALLATION.md](./INSTALLATION.md) · [OPERATOR_GUIDE.md](./OPERATOR_GUIDE.md) · [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)
