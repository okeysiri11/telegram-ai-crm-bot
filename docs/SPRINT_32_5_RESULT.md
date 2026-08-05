# Sprint 32.5 Result — Closed Beta Launch Preparation

**Track:** Closed Beta Launch Preparation  
**Date:** 2026-08-02  
**Status:** Complete (launch readiness track)  
**Version:** `32.5-closed-beta`

## Naming collision

Historical **Sprint 32.5** = Enterprise Intelligence Layer (`ENTERPRISE_INTELLIGENCE_32_5.md`, `enterprise-intelligence/`).  
Those docs and tests are **untouched**. This RESULT is the **Closed Beta** track only.

## Objective

No major new functionality — integration, stability, usability, bug fixing, launch readiness so a browser demo completes a full user journey.

## Delivered

### Enterprise City

- Security building → `/identity/security` (real Security Center)
- HR building → `/identity/users` (no HR placeholder)
- Marketing building → `/production-studio?studio=ads`
- `/security` route redirects to `/identity/security`
- Beta Home City copy updated to live City CTAs

### Owner Dashboard

- Replaced stub labels `"identity"` / `"live"` with session-derived user/org counts
- Expanded metrics: Security, Queues, API, DB, Redis, Providers, AI Usage
- God Mode: security + providers cards
- `OWNER_SUBSYSTEMS` expanded for beta module coverage

### Closed Beta catalog

- `closedBetaCatalog.ts` → sprint **32.5**, version `32.5-closed-beta`, Security + Register surfaces

### Documentation

`CLOSED_BETA_GUIDE.md` · `FIRST_USER_JOURNEY.md` · `KNOWN_LIMITATIONS.md` · `RELEASE_CHECKLIST.md` · `SPRINT_32_5_RESULT.md`  
Updated: `CLOSED_BETA.md`, `ARCHITECTURE_MAP.md`, Product Bible

## Quality

```bash
cd src/web && npm run lint && npm test && npm run build
```

## Definition of Done

| Criterion | Status |
|---|---|
| City buildings open real modules | ✓ |
| Owner Dashboard shows live-derived info | ✓ |
| Login → wizard → Owner → City journey documented | ✓ |
| No placeholder City security/HR destinations | ✓ |
| Release docs pack | ✓ |
| Intelligence 32.5 docs preserved | ✓ |
