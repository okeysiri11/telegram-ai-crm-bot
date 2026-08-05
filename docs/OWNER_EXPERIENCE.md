# Sprint CQ-30.7 — Owner & Admin Experience Review

**Scope:** can an Owner actually manage Platform/Organizations/Users/AI/Knowledge/Marketplace/
Security/City/Production without confusion? Admin Mode reviewed comparatively (no dedicated document
requested in this sprint's brief; folded in here as the closest real relative). Documentation only,
`src` not modified.

## 1. Real Owner navigation — 13 items, evaluated against the brief's 9

```
Панель владельца (/owner) · Состояние платформы (/health) · Архитектура (/kernel) ·
Аудит (/platform-builder/governance) · Центр безопасности (/identity/security) ·
Среда AI (/ai-agents) · Граф знаний (/platform-builder/knowledge) · Среда города (/city) ·
Разработчик (/platform-builder/builder-studio) · Журналы (/command-runtime) ·
Флаги функций (/settings?tab=flags) · Администрирование (/admin) · God Mode (/platform-builder/god-mode)
```

| Brief item | Real coverage | Confusion risk |
|---|---|---|
| Platform | Real "Состояние платформы" (Platform Health) | None — clearly labeled |
| Organizations | **No dedicated Owner-nav item** — closest is "Администрирование" (`/admin`), unconfirmed whether org management lives there | **Real gap** — an Owner looking for "manage organizations" has no direct-labeled path in the real 13-item Owner nav |
| Users | **No dedicated Owner-nav item** either — the *general* sidebar has "Пользователи" (`/identity/users`), not owner-scoped | Minor — findable, but not surfaced as an Owner-specific concern despite being a natural Owner responsibility |
| AI | Real "Среда AI" (`/ai-agents`) — same route as the general sidebar's `ai_agents` item | None functionally, but see §2 below |
| Knowledge | Real "Граф знаний" (Knowledge Graph, `/platform-builder/knowledge`) — **different route** from the general sidebar's "Знания" (`/knowledge`) | **Real confusion risk** — two different real destinations both plausibly answering "where do I manage Knowledge," one Owner-scoped, one general |
| Marketplace | **No dedicated Owner-nav item** | Not necessarily a gap — Marketplace may not need Owner-specific management, but worth confirming deliberately, not by omission |
| Security | Real "Центр безопасности" (Security Center) | None — clearly labeled, matches real `SecurityCenterPage.tsx` (CQ-30.1) |
| City | Real "Среда города" (`/city`) — same route as the general sidebar's `city` item | Same pattern as AI — see §2 |
| Production | **No dedicated Owner-nav item** — Production Studio only in the general sidebar | Not necessarily a gap, same reasoning as Marketplace |

## 2. The recurring pattern: Owner-scoped nav items that route identically to general ones

"Среда AI" and "Среда города" both route to the exact same paths (`/ai-agents`, `/city`) as their
general-sidebar counterparts. This is not necessarily wrong — an Owner might reasonably expect the same
screen with elevated permissions applied automatically — but it means the *navigation label itself*
promises something Owner-specific ("Среда," meaning "Environment," implies a different, more
administrative view) that the *route* doesn't confirm. Worth a direct product decision: either these
routes render a genuinely different Owner-elevated view at the same URL (fine, just undocumented), or
the labeling should be adjusted to not imply a different destination than the general nav item.

- **Why:** two navigation items with different labels routing to the same URL is either intentional
  (permission-elevated same-page rendering) or a real missed opportunity to build a distinct Owner view.
- **Impact:** Medium — an Owner could reasonably expect something different behind "Среда AI" than
  what a regular AI-Agents user sees, and be confused if it's identical.
- **Priority:** P1.
- **Complexity:** S to confirm/document; M if a genuinely distinct Owner view needs building.
- **Evidence:** `enterpriseRuNav.ts:45-46` (owner_ai, owner_city) vs. `:19` (ai_agents), `:17` (city).

## 3. Owner Dashboard vs. God Mode — restated from `docs/UX_AUDIT.md`

Two real, separate destinations (`/owner` and `/platform-builder/god-mode`) both plausibly answer "the
Owner experience." This document adds one more piece of evidence: God Mode's route lives under
`/platform-builder/`, the same URL namespace as three other Owner items (Аудит, Граф знаний,
Разработчик) — suggesting God Mode may be a Platform-Builder-specific power-user surface, distinct
from the general Owner Dashboard's broader composite view (`docs/OWNER_MODE_UX.md`, CQ-30.1). If that's
the intended relationship, it should be stated explicitly somewhere a new Owner would see it (e.g., a
tooltip distinguishing "Owner Dashboard: your overview" from "God Mode: advanced platform controls").

## 4. Admin Mode, compared

The real Role Switcher's "Администратор" maps to `["administrator", "admin", "system_admin"]` — a
single Admin persona covering what the backend's `EngineRoleCode.ADMIN` also represents. Unlike Owner,
Admin has **no dedicated navigation array** in `enterpriseRuNav.ts` — an Admin presumably sees the
general 23-item sidebar with some items hidden (per `docs/ROLE_NAVIGATION.md`'s hidden-not-disabled
principle, CQ-30.1), not a curated Admin-specific set the way Owner gets. This is a reasonable design
choice (Admin's job is largely "the general sidebar, minus Owner-only items," not a distinct
information architecture) — flagged here as confirmed-by-omission, not as a defect.

## Non-goals

- No redesign of the Owner navigation array — findings are label/route-clarity questions, not a
  structural critique.
- No Admin-specific navigation array proposed — §4's finding is that the current "general sidebar minus
  hidden items" design is reasonable, not that Admin needs its own curated array like Owner has.

## Related documents

`src/web/src/navigation/enterpriseRuNav.ts` (real), `docs/OWNER_MODE_UX.md` (CQ-30.1, the composite
Owner Dashboard design this document's §3 references), `docs/UX_AUDIT.md` (CQ-30.7 sibling, the Owner
Dashboard/God Mode finding restated here with route-namespace evidence).
