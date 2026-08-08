# Sprint 42.3 — Client Demo Polish & UX Review

**Status:** COMPLETE (audit + polish)  
**Mode:** Real client experience · final polish only  
**Baseline:** Sprint 42.0–42.2 (workspace · multi-role · adaptive shell)  
**Date:** 2026-08-06  

---

## Verdict

| Score | Value |
|-------|-------|
| **Overall UX** | **7.6 / 10** |
| **Client Readiness** | **7.8 / 10** |
| **Recommendation** | **NEEDS POLISH** → ready for guided demos after the fixes in this sprint; not yet “walk in alone” production-client ready |

**Also see:** [SPRINT_42_3_AUTO_HUMAN_UX.md](./SPRINT_42_3_AUTO_HUMAN_UX.md) — Auto module Human-First (AI bar, voice, Ops Center).

Guided demo with `travel@globefly.demo` / password `demo` (locale RU, view mode Client) is **viable**. Unattended first-time clients still hit residual English in deep enterprise pages and incomplete landings on Tasks / Calendar / Settings.

---

## Scope reviewed

| Module | Landing | Client allowlist | First-action (5s) | Notes |
|--------|---------|------------------|-------------------|-------|
| CRM | Yes | Yes | Strong CTA «Создать клиента» | Demo flow OK |
| Documents | Yes | Yes | Upload CTA | Deep link works |
| Knowledge | Yes | Yes | Fixed self-loop CTA | RU title |
| Analytics | Yes | Yes | Dashboard CTA | RU title |
| AI | Yes | Yes | Deep link `?view=assistant` | Landing OK |
| Crypto | Yes | Manager+ | OTC CTA | Vertical allowlist fixed |
| Drone | Yes | Manager+ | Create drone | Vertical allowlist fixed |
| Auto | Yes | Manager+ | Add vehicle | Vertical allowlist fixed |
| Legal | Yes | Client (legal persona) | Contract CTA | `/workspace/legal` allowlisted |
| Agro | Yes | Manager+ | Farm CTA | RU + офлайн string |
| Cafe | Yes | Manager+ | Orders | Niche vertical |
| Platform | Yes | Owner+ | Builder | Hidden from client chrome |
| Owner | Yes | Owner+ | Overview deep link | Hidden from client |
| Settings | Help only | Yes | Weak | Needs dedicated landing (deferred) |
| Marketplace | Yes | Client (seller) | Product CTA | Allowlisted |
| Search | Page | Yes | RU chrome (this sprint) | OK for demo |
| Support | Redirect → Knowledge | Yes | Fixed dead end | `/support` → knowledge |

---

## Client demo flow (simulated)

| Step | Friction before | After 42.3 |
|------|-----------------|------------|
| Login | EN «Open Demo Workspace», port noise | RU CTA, cleaner account list |
| Open CRM | Landing clear | Unchanged (good) |
| Create Client | Deep link works | Unchanged |
| Create Deal | Via CRM views | Unchanged |
| Analytics | EN title | RU «Аналитика» |
| Documents | EN title | RU «Документы» |
| Search | Fully English page | RU i18n |
| AI Assistant | Landing CTA looped to itself | `?view=assistant` |
| Logout | Via user menu | OK |

---

## Critical issues

| # | Issue | Status |
|---|--------|--------|
| C1 | Empty-state «Демо-данные» (`?demo=1`) was a no-op | **Fixed** — `demo=1` treated as deep link |
| C2 | Dashboard Quick Actions linked to blocked routes (`/projects`, `/city`, …) | **Fixed** — filtered by view mode |
| C3 | `/support` allowlisted with no route | **Fixed** — redirect to Knowledge |
| C4 | Legal client persona blocked from `/workspace/legal` | **Fixed** — allowlist |
| C5 | Login primary demo CTA in English | **Fixed** |
| C6 | Knowledge / AI primary CTAs looped to the same landing | **Fixed** |

---

## Medium issues

| # | Issue | Status |
|---|--------|--------|
| M1 | Landing titles English under `locale=ru` | **Fixed** (client hubs) |
| M2 | Tasks / Calendar / Settings / Notifications lack ModuleLandingView | **Open** — help bar only |
| M3 | Double orientation chrome on landings | **Fixed** — bar hidden when landing owns UI |
| M4 | Trail hardcoded «Owner» | **Fixed** → `role.owner` / Владелец |
| M5 | Dock labels English; defaults included drone/crypto | **Fixed** RU + client-safe defaults |
| M6 | ShellRuntimeBar (CPU/Mem/Jobs) on client | **Fixed** — hidden for client/manager chrome |
| M7 | Focus Mode button on client header | **Fixed** — hidden for client/manager |
| M8 | Business module badge «Sprint 30.8» / API source | **Fixed** → «Рабочий модуль» |
| M9 | Search Workspace English | **Fixed** |
| M10 | Onboarding module chips English | **Fixed** |
| M11 | Manager verticals (crypto/drone/auto/agro) not allowlisted | **Fixed** |

---

## Minor issues

| # | Issue | Status |
|---|--------|--------|
| m1 | Agro «offline» English mix | Fixed |
| m2 | Login port suffixes (`:3001`) | Removed from select labels |
| m3 | Quick Actions showed raw routes | Hidden |
| m4 | Sidebar `Intelligent Navigation` / `Owner` | RU |
| m5 | Error boundaries still English | Open (rare path) |
| m6 | Platform stats `ok` / `Runtime` English | Open (owner-only) |
| m7 | Cafe has 2 stats (others usually 3) | Acceptable |
| m8 | DevRoleSwitcher in header (dev builds) | Acceptable for demos |

---

## Quick wins shipped this sprint

1. Login: «Открыть демо-пространство» + RU errors  
2. Quick Actions filtered by `isRouteAllowedForViewMode`  
3. Hide `ShellRuntimeBar` for client/manager chrome  
4. RU dock labels + safer defaults  
5. RU landing titles for major hubs  
6. `demo=1` deep-link handling  
7. Skip duplicate `PageOrientationBar` on landings  
8. Onboarding chips RU; `/support` redirect  
9. Search page i18n  
10. Hide Focus for client; Settings gear always available  
11. Strip sprint/source badges from business shells  
12. Vertical allowlists for legal (client) and OTC/drone/auto/agro (manager)  
13. Fix Knowledge / AI / Owner primary CTA self-loops  

---

## Suggested redesigns (next polish sprint)

1. **Dedicated landings** for Tasks, Calendar, Settings, Notifications (same ModuleLandingView pattern).  
2. **Client dashboard Quick Actions** as a curated RU set (not a filtered enterprise list).  
3. **First-run coach marks** on CRM landing (single spotlight on primary CTA).  
4. **ErrorBoundary / RouteErrorBoundary** RU strings.  
5. **Uniform spacing tokens** audit (`ews-module-hero` padding vs deep CRM tabs).  
6. Screenshots pack for sales demos (login → CRM → deal → analytics → AI).

---

## Screenshots

Not captured in-repo (headless audit). Recommended capture set for sales:

1. Login with demo accounts (RU)  
2. CRM landing (Where / AI guide / primary CTA)  
3. CRM clients create flow  
4. Analytics landing  
5. Documents landing  
6. Search workspace (RU)  
7. AI landing + assistant  
8. Client chrome without runtime bar  

---

## Acceptance checklist

| Criterion | Result |
|-----------|--------|
| Every major screen reviewed | Yes (code + catalog walkthrough) |
| No unexplained pages (client path) | Mostly — Settings/Tasks still thin |
| No unnecessary UI (client) | Improved (runtime/focus/ops hidden) |
| Russian localization verified | Chrome + landings + search; residual EN in deep enterprise |
| Navigation intuitive | Yes for CRM→Docs→Analytics→AI |
| Client knows what to do in 5s | Yes on module landings; weaker on Settings/Tasks |
| Final UX report generated | **This document** |
| No new enterprise functionality | Confirmed — polish / allowlist / i18n only |

---

## Architectural decisions

| Decision | Why | Rejected |
|----------|-----|----------|
| Filter Quick Actions by view mode instead of a new client catalog | Reuses allowlist; no duplicate action defs | Hard-coded client-only list (faster but drifts) |
| Treat `demo=1` as deep link | Minimal change; empty CTA becomes live module | Separate demo seed service (enterprise feature) |
| Redirect `/support` → Knowledge | Avoids new Support module in polish sprint | Empty Support page |
| Extend CLIENT/MANAGER allowlists for verticals | Unblocks legal/seller/crypto demo personas | Per-user dynamic allowlist (larger change) |

---

## Tests

- `src/web/src/ux/client_demo_42_3.test.ts` — titles, deep CTAs, allowlists, dock RU, search i18n  
- Regression: prior 42.0 / 42.1 / 42.2 suites  

---

## Files touched (polish)

- `auth/pages/LoginPage.tsx`  
- `workspace-engine/QuickActionsPanel.tsx`  
- `layouts/FullLayout.tsx`  
- `workspace-chrome/workspaceDockStore.ts`  
- `ux-revolution/viewModeCatalog.ts`  
- `modules/SearchWorkspacePage.tsx`, `WorkspaceLandingGate.tsx`, `ModuleHubRoute.tsx`, `moduleLandingCatalog.ts`  
- `help/PageOrientationBar.tsx`  
- `enterprise-business/BusinessModuleShell.tsx`  
- `navigation/TopNavigation.tsx`, `Sidebar.tsx`  
- `multi-role/ClientOnboardingPage.tsx`  
- `i18n/messages.ts`  
- `App.tsx` (`/support` redirect)  
- `ux/client_demo_42_3.test.ts`  
- `docs/SPRINT_42_3_UX_REVIEW.md`  

---

## Recommendation detail

**NEEDS POLISH** means: safe for **facilitated client demos** (GlobeFly travel path) after this sprint’s fixes.  

Promote to **READY** when:

1. Tasks / Calendar / Settings landings exist  
2. Error boundaries localized  
3. Spot-check of deep CRM/Documents screens shows no EN chrome badges  
4. Sales screenshot pack reviewed by a non-engineer  

Until then, keep a facilitator on the call for Settings and any vertical outside travel CRM.
