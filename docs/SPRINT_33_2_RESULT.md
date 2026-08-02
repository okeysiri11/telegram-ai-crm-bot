# Sprint 33.2 — Intelligent Navigation

**Frontend only.** Left sidebar redesign: collapsible accordion groups.

## Groups

| Group | Simple | Pro | Owner |
|-------|--------|-----|-------|
| Workspace | yes | yes | yes |
| Business | yes | yes | yes |
| AI | yes | yes | yes |
| Enterprise City | — | yes | yes |
| Platform | — | yes | yes |
| Owner | — | — | yes |

## Rules

- One group expanded at a time (`useNavAccordionStore`)
- Expanded group key: `localStorage.ewp_nav_accordion_group_v1`
- Panel animation: **150ms** (`intelligentNav.css`)
- Active route highlighted; owning group auto-expands on navigation
- Search / Ctrl+K still indexes all modules (unchanged palette)
- Routes unchanged; no backend changes

## Package

- `src/web/src/ux-revolution/intelligentNavGroups.ts`
- `src/web/src/ux-revolution/navAccordionStore.ts`
- `src/web/src/ux-revolution/NavAccordionGroup.tsx`
- `src/web/src/navigation/Sidebar.tsx` (refactored)

## Collision

Preserve Integration Hub / other **33.1** docs; this track is **33.2**.
