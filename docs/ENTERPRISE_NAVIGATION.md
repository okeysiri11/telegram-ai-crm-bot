# Enterprise Navigation

**Sprint:** 30.7 · Enterprise Workspace Russian UI

> **Note:** `docs/NAVIGATION.md` is the drone resilience navigation doc (Sprint 11.9). This file is the Enterprise Web sidebar / shell navigation map.

## Sources of truth

| Concern | File |
|---------|------|
| Sidebar (RU) | `src/web/src/navigation/enterpriseRuNav.ts` → `ENTERPRISE_RU_SIDEBAR` |
| Owner nav | `OWNER_RU_NAV` |
| Quick actions | `RU_QUICK_ACTIONS` |
| Breadcrumbs | `BREADCRUMB_LABEL_RU` |
| Role homes | `src/web/src/navigation/roleHome.ts` |
| Search index | `src/web/navigation/managers/searchIndex.ts` |
| Shell sidebar | `src/web/src/navigation/Sidebar.tsx` |
| Top bar | `src/web/src/navigation/TopNavigation.tsx` |

## Features

- **Left Navigation** — every item routes to a live module (`/crm`, `/tasks`, `/city`, …)
- **Favorites / Recent** — workspace engine + navigation history
- **Notifications** — top bar → `/notifications`
- **Global Search** — top search + `/search` + Cmd/Ctrl+K
- **Breadcrumbs** — Russian segment labels
- **Role switcher / Org selector** — top bar (RU)

## Aliases

| Alias | Target |
|-------|--------|
| `/city` | Enterprise City (same as `/enterprise-city`) |
| `/ai` | `/ai-agents` |
| `/admin` | Admin dashboard |
| `/dashboards/admin` | → `/admin` |

## Rule

No menu item may use empty `#` anchors or placeholder-only pages.

## Related

[WORKSPACE.md](./WORKSPACE.md) · [COMMAND_PALETTE.md](./COMMAND_PALETTE.md) · [UI_NAVIGATION.md](./UI_NAVIGATION.md) · [NAVIGATION.md](./NAVIGATION.md) (drone)
