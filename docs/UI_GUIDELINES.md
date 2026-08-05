# UI Guidelines

**Sprint:** 31.1 · Default locale: **Russian**

## Language

- Default UI language is Russian for Closed Beta menus, dialogs, buttons, notifications, sidebar, settings
- Prefer existing `enterpriseRuNav`, `messages.ru`, and RU labels in studio chrome
- Product names (CRM, Runtime, Desktop) may stay Latin where already established

## Composition

- Reuse Design System (`@/ui`, EDS/EDL/EDM) — do not invent parallel button/card systems
- Role dashboards compose `RoleDashboardPolish` + section link cards
- City is the spatial navigator; dashboards are operational hubs

## Interaction

- Module open: route to real pages (ModuleHub / enterprise-business)
- Loading: skeletons (`edm-skeleton`) or short RU helper text
- Empty states: honest RU copy, CTA to a live route
- Avoid “скоро” placeholders on shipped Beta surfaces

## Motion

- Page enter: `edm-page` / `edm-page-soft`
- Sidebar / palette: existing shell transitions
- City: hover lift, select settle, flowing links — gated by reduced motion

## Accessibility

- Breadcrumbs and minimap have `aria-label` in Russian
- Health meters use `role="meter"`
- Do not rely on color alone for critical/warning (labels + badges)

## Related

- `VISUAL_SYSTEM.md`, `ENTERPRISE_CITY_UI.md`, `OWNER_GOD_MODE.md`
