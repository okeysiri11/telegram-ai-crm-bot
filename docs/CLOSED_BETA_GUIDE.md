# Closed Beta Guide

**Sprint:** 32.5 — Closed Beta Launch Preparation  
**Version:** `32.5-closed-beta`  
**Collision:** Enterprise Intelligence also uses Sprint **32.5** (`ENTERPRISE_INTELLIGENCE_32_5.md`) — that track is preserved. This guide is the **Closed Beta launch** track.

**Extends:** [`CLOSED_BETA.md`](./CLOSED_BETA.md) (Sprint 31.0 RC), [`FIRST_RUN.md`](./FIRST_RUN.md), [`PILOT_CHECKLIST.md`](./PILOT_CHECKLIST.md)

## Goal

Open ADOS in a browser and complete a working user journey without broken navigation or placeholder city destinations.

## Quick start

1. Start API + web (see [`FIRST_RUN.md`](./FIRST_RUN.md) / [`INSTALLATION.md`](./INSTALLATION.md)).
2. Open `/login` — Google or email (demo auth when `VITE_DEMO_AUTH` enabled).
3. Complete `/onboarding/first-entry` (role → organization/workspace → ready).
4. Land on Owner `/owner` (or role home).
5. Open `/city` — click buildings → real modules.
6. Exercise AI Studio / Production Studio / Security Center `/identity/security`.

## Surfaces

Canonical checklist: `src/web/src/closed-beta/closedBetaCatalog.ts`.

## Related

[`FIRST_USER_JOURNEY.md`](./FIRST_USER_JOURNEY.md) · [`RELEASE_CHECKLIST.md`](./RELEASE_CHECKLIST.md) · [`KNOWN_LIMITATIONS.md`](./KNOWN_LIMITATIONS.md) · [`SPRINT_32_5_RESULT.md`](./SPRINT_32_5_RESULT.md)
