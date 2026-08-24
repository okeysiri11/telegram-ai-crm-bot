# Sprint MOBILE 1.1 — Current mobile home actually works

Visual style of the existing mobile home is unchanged (dark navy + turquoise, rounded cards, 44px targets, bottom nav). Dead controls now navigate.

## What shipped

1. **Primary CTAs** use real routes via `navigate()` (no `<a><button>`). Owner «Открыть рабочее пространство» / «Открыть панель» go to `/workspace`, not a self-link to `/dashboard`. AI goes to `/ai-agents`. Settings → `/settings`. Ещё → overflow sheet. Избранное → existing favorites sheet.
2. **`/workspace` on mobile** is a hub of vertical cards (Авто, Агро, Crypto, Lawyer, Beauty, Cafe, …). Tap sets the vertical and opens that workspace.
3. **Owner mobile** is system mode copy («Режим · Владелец системы · Выберите рабочее пространство»), continue-work, important today, workspace cards, quick actions, favorites — not desktop God Mode. `/owner` uses a compact platform list.
4. **Bottom nav:** Главная `/dashboard`, Workspace `/workspace`, **+** create sheet, Уведомления `/notifications`, Ещё overflow. Active item highlighted.
5. **Create sheet «Создать»** is context-sensitive (global / AUTO ops views / AGRO ops views). Routes stay on mobile cabinets (`?view=`), not desktop-only forms.
6. **Важное сегодня** uses live notification counts only. Empty copy: «На сегодня критичных событий нет.»
7. **WorkspaceSlotBanner** (demo CTA + `:5180` port) is hidden on mobile. Demo CTA on home appears only if the GlobeFly demo user exists; disabled if already in that session.
8. **Desktop sidebar is not mounted** at ≤767px. `MobileRouteGate` keeps desktop layouts on `md+`.
9. **API** remains relative `/api` (public Cloudflare-compatible). No localhost hrefs in mobile nav.

## Architectural decisions

- Extend `src/web/src/shell/mobile/*` instead of a new platform package.
- Do not change `/api/v1` or backend permissions. Same catalogs and ops cabinets.
- Do not rename the catalog vertical `owner`; only the mobile copy changes.

## Desktop

Unchanged at ≥768px: command center dashboard, owner God Mode, workspace KPI home, sidebar.

AUTO 1.9 was not started.
