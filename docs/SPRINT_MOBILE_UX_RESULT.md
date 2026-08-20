# Sprint — Mobile-first ADOS Enterprise UX

Desktop sidebar + business logic are unchanged. Mobile (≤767px) uses a dedicated chrome layer on the same app, routes, catalogs, and API.

## What changed

1. **Demo/test notification spam removed.** `notificationStore` starts empty. Fixtures (`AI insight ready`, `Provider timeout`, …) load only with `VITE_DEBUG_NOTIFICATIONS=true` or `localStorage.ADOS_DEBUG_NOTIFICATIONS=1`. Toasts show only *new* events, max 2, auto-dismiss (errors stay until dismissed). Activity panel no longer fills empty tabs with demo seed.
2. **Mobile shell:** header `☰ ADOS [Workspace] 🔔 ⋮`, workspace drawer from current vertical/ops nav (not agro-only), in-app back, bottom nav, More sheet, workspace switcher.
3. **Owner:** platform admin links live under **Управление платформой**, not on mobile home.
4. **Mobile Home:** workspace + role, 4–6 quick actions, compact Избранное row → sheet, «Важное сегодня», analytics collapsed.
5. **Ops tables:** card/list on mobile in `BusinessCabinetShell` (Auto/Agro/Legal/Crypto/Beauty/Cafe). Desktop tables unchanged.
6. **Forms/buttons/overflow:** 44px controls, single-column forms, `overflow-x: hidden` on the page, table min-width lifted on small screens.
7. **AI Agents:** compact status on mobile; metric grids stay on `md+`.
8. **DEMO badge** for `@demo.` / `demo` tenant — does not block navigation.

## Components

| New / extended | Role |
|---|---|
| `src/web/src/shell/mobile/*` | Mobile chrome, home, drawer, bottom nav |
| `src/web/src/layouts/FullLayout.tsx` | Desktop chrome vs mobile chrome |
| `src/web/src/pages/DashboardPage.tsx` | Mobile home |
| `src/web/src/notifications/notificationStore.ts` | No production seed |
| `src/web/src/workspace-chrome/UnifiedToastStrip.tsx` | Queue, auto-dismiss |
| `src/web/workspace/business-ops/BusinessCabinetShell.tsx` | Registers ops nav + mobile cards |
| `src/web/src/ai-runtime/AIAgentCenterPage.tsx` | Compact mobile summary |
| `src/web/design-system/styles/edl.css` | Mobile table/control tweaks |

## Desktop

Sidebar, header, favourites dock, command-center dashboard, ops tables remain at `md+` (768px).

AUTO 1.9 was not started.
