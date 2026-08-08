# Sprint 41.1 — First Client Journey (GlobeFly)

**MODE:** IMPLEMENTATION + UX  
**BASELINE:** post-40.4 (View Mode shipped in this sprint; 41.0 not a separate release)  
**Date:** 2026-08-06  
**Status:** COMPLETE  
**Client:** GlobeFly (first commercial candidate)

---

## Objective

Transform the owner-oriented shell into a **client-ready** experience: View Modes (UI only), GlobeFly demo tenant, Client navigation, Russian chrome, measured first-client journey.

---

## Journey map

```text
Login (client@globefly.demo / demo)
  → Dashboard (GlobeFly KPIs, no builders)
  → CRM / Create Lead
  → Open Client
  → Documents (upload/list)
  → AI Assistant
  → Reports (/analytics)
  → Logout
```

| Step | Route | Clicks (est.) | Time (est.) | Confusion | Severity |
|------|-------|---------------|-------------|-----------|----------|
| 1 Login | `/login` | 3 | ~20s | Demo default now GlobeFly Client | Low (fixed) |
| 2 Dashboard | `/dashboard` | 1 | ~5s | Previously mixed “Runtime/City” | High → Fixed |
| 3 Create Lead | `/crm?view=leads` | 3–5 | ~45s | OK for operators | — |
| 4 CRM / Client | `/crm?view=clients` | 2 | ~20s | Seeded GlobeFly clients | — |
| 5 Documents | `/documents` | 2–4 | ~40s | Upload path still module-dependent | Medium |
| 6 AI chat | `/ai-agents` | 2 | ~30s | Header AI no longer opens Builder Concierge | High → Fixed |
| 7 Report | `/analytics` | 1–2 | ~20s | Hub depth limited | Medium |
| 8 Logout | `/auth/logout` | 1–2 | ~5s | — | — |

Probe: [`docs/acceptance_41_1_probe.json`](acceptance_41_1_probe.json) · [`scripts/acceptance_probe_41_1.py`](../scripts/acceptance_probe_41_1.py)

---

## Screenshots / layout notes

Capture unavailable in CI agent; layout after 41.1:

- **Header:** Logo · Search · Company (GlobeFly) · Language · **View mode** · Notifications · AI status · Profile  
- **Sidebar (Client):** Workspace + Business + AI only — no Platform / Owner / City / Builders  
- **Right panel:** Collapsed by default; opens to Уведомления / Активность / AI / Система  
- **Dashboard (GlobeFly Client):** Welcome RU + KPI cards + working modules (no Enterprise City / Production Studio)

---

## What shipped

### View Mode (UI only — permissions unchanged)

| Mode | Behavior |
|------|----------|
| Client | Allowlisted business routes only |
| Manager | Client + projects/ERP/marketplace/knowledge |
| Company Administrator | Manager + admin/identity/health (no builders/runtime) |
| Platform Owner | Everything |
| Developer | Everything (diagnostics focus) |

Files: `viewModeCatalog.ts`, `viewModeStore.ts`, `ViewModeRouteGuard.tsx`, Sidebar/TopNavigation/FullLayout wiring.

### GlobeFly demo

- Tenant `globefly` / label **GlobeFly**  
- Users: `owner|admin|manager|sales|operator|client@globefly.demo` / password `demo`  
- Seed: clients, leads, deals, documents, invoices, knowledge, AI prompts, dashboard KPIs  
- Login defaults to `client@globefly.demo` + tenant GlobeFly when demo auth on  
- After login: View Mode Client, locale `ru`, org GlobeFly

### Localization (Client chrome)

- New keys: `viewMode.*`, `activity.*`, `ops.*`, `globefly.welcome`, `common.close|back|next`, statuses  
- Activity panel, tab menu, ops strips, builder “Планируется”, login Email label via `t()`  
- Client shell hides English platform strips / LeftDock / runtime bar

### Help

- `moduleHelpCatalog.ts` + `ModuleHelpIcon` on dashboard (purpose / why / result / workflow / difficulty / time / example)

---

## Issues found → fixed

| ID | Problem | Fix | Priority |
|----|---------|-----|----------|
| GF-41-001 | No View Mode; Role switcher looked like security | View Mode selector + allowlists | Critical |
| GF-41-002 | Client saw Builders / Runtime / City / strips | Filter nav + hide strips in Client/Manager | Critical |
| GF-41-003 | AI header → Platform Builder Concierge | Navigate to `/ai-agents` | High |
| GF-41-004 | Right panel always open (noise) | Default collapsed + autoHide | High |
| GF-41-005 | English Activity Center / Coming soon | RU i18n + builder статусы | High |
| GF-41-006 | No GlobeFly tenant/demo user | Demo package + demoAuth | Critical |
| GF-41-007 | Soft open of hidden routes | `ViewModeRouteGuard` → `/dashboard` | Medium |

---

## Remaining blockers / gaps

| ID | Issue | Priority |
|----|-------|----------|
| GF-41-R01 | Document upload/download E2E not API-proven for GlobeFly | Medium |
| GF-41-R02 | Analytics hub not a dedicated GlobeFly funnel board | Medium |
| GF-41-R03 | Some module body copy / seed activity strings still English | Medium |
| GF-41-R04 | Help ⓘ not yet on every module page (catalog ready; dashboard wired) | Low |
| GF-41-R05 | Marketing tags / SMTP (from 40.x) unchanged | Low–Medium for commercial |

---

## UX recommendations

1. Wire `ModuleHelpIcon` into CRM / Documents / AI / Analytics page headers.  
2. Persist company profile edit (logo) to a dedicated settings form backed by existing org APIs when available.  
3. Replace remaining English seed activity titles with RU when locale is `ru`.  
4. Add click-telemetry counters on journey CTAs for live UX measurement.  
5. Keep View Mode clearly labeled “только интерфейс” near selector to avoid permission confusion.

---

## Navigation complexity

- Client sidebar groups: typically **3** (workspace / business / AI) vs Owner **6**.  
- Journey critical path: **~15–20 clicks** end-to-end for a trained user.  
- Soft-redirect prevents dead-ends into builders.

---

## Missing translations (Client path)

Mostly addressed for shell chrome. Remaining: some CRM/Documents internal English labels, Activity seed titles, occasional Badge tone labels (`info`). Tracked as GF-41-R03.

---

## Quality gates

| Gate | Status |
|------|--------|
| Frontend unit tests (View Mode + GlobeFly + journey smoke) | PASS |
| Docker / Health / Ready | PASS (probe) |
| Localization Client chrome keys | PASS |
| Role / View Mode preview | PASS |
| SPA journey routes HTTP 200 | PASS |
| Backend APIs / schema | Unchanged |

---

## Readiness score (first commercial client — GlobeFly operator UX)

| Area | Score |
|------|------:|
| Login + demo tenant | 95% |
| Client View Mode / nav | 92% |
| CRM journey | 88% |
| Documents | 70% |
| AI Assistant entry | 90% |
| Reports | 75% |
| RU chrome (Client) | 90% |
| Help system | 80% |

**Overall GlobeFly first-client UX: ~86%** — READY for guided pilot with Client View Mode; not yet turnkey for unsupervised commercial go-live until documents E2E + analytics depth (R01/R02).

**Verdict:** READY FOR FIRST COMMERCIAL CLIENT **pilot** (guided). Unsupervised go-live still gated by R01–R02 and 40.x marketing/SMTP items.

---

## Files touched (primary)

- `src/web/src/ux-revolution/viewModeCatalog.ts`, `viewModeStore.ts`, `ViewModeRouteGuard.tsx`, `viewMode_41_1.test.ts`
- `src/web/src/demo/globefly/*`
- `src/web/src/navigation/Sidebar.tsx`, `TopNavigation.tsx`, `enterpriseRuNav.ts`
- `src/web/src/layouts/FullLayout.tsx`
- `src/web/src/i18n/messages.ts`
- `src/web/src/shell/enterprise/ActivityPanel.tsx`, `shellLayoutStore.ts`
- `src/web/src/dashboard/BetaHomeDashboard.tsx`
- `src/web/src/help/*`
- `src/web/auth/pages/LoginPage.tsx`, `src/web/src/auth/demoAuthProvider.ts`, `authStore.ts`
- `scripts/acceptance_probe_41_1.py`, `docs/acceptance_41_1_probe.json`

---

## Architectural decisions

- View Mode is **orthogonal** to auth permissions (`authStore` never mutated by `setViewMode`).  
- GlobeFly seed is **frontend localStorage** (no DB migration) for demo speed.  
- Client chrome hides platform strips rather than deleting modules (Owner/Developer still full).
