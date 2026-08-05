# Sprint 27.1 — Enterprise Web Platform Foundation

**Phase:** 1 — Application Shell & Dashboard  
**App:** `src/web` (`enterprise-web-platform` **9.5.0**)  
**Date:** 2026-07-29

## Goal

Deliver a production Application Shell as the primary Enterprise UI surface — not a prototype — while extending the existing web platform (no architecture rewrite).

## Implemented

### Application Shell (5 regions)

| Region | Implementation |
|--------|----------------|
| Top Header | `TopNavigation` — ADOS Enterprise logo, global search, breadcrumbs, notifications, AI status, user, theme (Light/Dark/Auto), settings |
| Left Sidebar | `Sidebar` + `ENTERPRISE_SHELL_NAV` — all required sections with icons |
| Main Workspace | `FullLayout` scrollable workspace (existing strips + routes preserved) |
| Right Activity Panel | `ActivityPanel` — Recent / Notifications / Running Tasks / AI Messages / System Events |
| Bottom Status Bar | `StatusBar` — Runtime, API, Database, Providers, Voice, MCP, Queue, Build, Version (color dots) |

Full-viewport (`100dvh`) layout with responsive breakpoints for Full HD → 2K / ultrawide / 4K.

### Dashboard

`EnterpriseModuleGrid` on `/dashboard`: CRM, ERP, Projects, AI Agents, Knowledge, Analytics, Finance, Marketplace, Automation, Security — each with icon, description, stats, Open CTA.

### Themes

Light · Dark · Auto (`system` + OS preference listener). Persisted in `ews_theme_mode_v1`.

### Performance (reused)

Route-level `lazy` + `Suspense` in `App` / `FullLayout`, `ErrorBoundary` / `RouteErrorBoundary`, code-split strips.

### Design

Glass chrome (`enterpriseShell.css`): soft shadows, rounded corners, gradient shell background, hover motion — EDL/EDS tokens.

## Files created

- `src/web/src/shell/enterprise/enterpriseNav.ts`
- `src/web/src/shell/enterprise/ShellIcons.tsx`
- `src/web/src/shell/enterprise/shellLayoutStore.ts`
- `src/web/src/shell/enterprise/activityCatalog.ts`
- `src/web/src/shell/enterprise/statusCatalog.ts`
- `src/web/src/shell/enterprise/ActivityPanel.tsx`
- `src/web/src/shell/enterprise/StatusBar.tsx`
- `src/web/src/shell/enterprise/EnterpriseModuleGrid.tsx`
- `src/web/src/shell/enterprise/index.ts`
- `src/web/src/shell/enterprise/enterpriseShell.css`
- `src/web/src/dashboard/enterpriseModuleCards.ts`
- `docs/SPRINT_27_1_RESULT.md`

## Files changed

- `src/web/src/layouts/FullLayout.tsx`
- `src/web/src/navigation/Sidebar.tsx`
- `src/web/src/navigation/TopNavigation.tsx`
- `src/web/src/pages/DashboardPage.tsx`
- `src/web/src/theme/themeStore.ts`
- `src/web/src/shell/Providers.tsx`
- `src/web/src/index.css`
- `src/web/src/config/webConfig.ts`
- `src/web/src/dashboard/index.ts`
- `src/web/package.json`
- `src/web/README.md`

## Remaining (later phases)

- Wire StatusBar probes to live Runtime `/voice`, `/mcp`, queue APIs when Control Center proxy is unified with web Vite
- Deepen Activity Center with Socket.IO live stream
- Module cards stats from live Mission Control (currently seed + soft probes)
- Ultrawide density presets / user-resizable activity panel width

## Build result

```text
npm install  — OK (deps up to date)
npm run build — OK (tsc -b && vite build, ~537 modules)
npm test — OK (65 passed)
npm run lint — OK (tsc -b)
npm run dev — Vite on http://localhost:5180
```

Chunk size warning for main bundle remains (pre-existing); shell strips stay lazy-loaded.
