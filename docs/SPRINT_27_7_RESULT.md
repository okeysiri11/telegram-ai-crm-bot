# Sprint 27.7 — Enterprise Desktop Environment

**Phase:** Enterprise Platform v9  
**App:** `src/web` · sprint `27.7`  
**Constraint:** Extend existing architecture — no redesign of prior modules.

## Goal

Transform the workspace into a real **Enterprise Desktop** (canvas, dock, window manager, launcher, memory, keyboard) so the platform feels like an Enterprise OS rather than a traditional web app.

## Implemented

1. **Enterprise Desktop** — canvas, wallpaper system, layout profiles, icons, folders, shortcuts, drag & drop  
2. **Enterprise Dock** — pinned / running / recent, hover scale, running dots, badges, minimize/restore  
3. **Window Manager** — move, resize, minimize, maximize, restore, snap L/R, fullscreen, last position  
4. **Desktop Launcher** — CRM, ERP, Finance, Knowledge, AI Studio, Marketplace, Analytics, Settings, Enterprise City, Production Studio, Developer Tools  
5. **Workspace Memory** — `ews_desktop_session_v1` (windows, layout, dock, wallpaper, profile, workspace)  
6. **Keyboard** — Alt+Tab · Cmd/Ctrl+Space · Esc · Cmd/Ctrl+W · Cmd/Ctrl+Shift+T (+ Cmd/Ctrl+K palette)  
7. **Animations** — EDL overlay / dock scale only  
8. **Status integration** — notifications, AI, providers, runtime, jobs in menubar/dock  
9. **Performance** — lazy iframes, unmount minimized, scoped Zustand selectors  
10. **Docs** — `DESKTOP.md`, `WINDOW_MANAGER.md`, this report

## Architecture decisions

1. New package `src/enterprise-desktop/` (same pattern as live-dashboard / command-center-runtime).  
2. Standalone `/desktop` route (no FullLayout) — Classic UI remains at `/dashboard`.  
3. Windows load modules via same-origin iframe + `?embed=1` — zero rewrite of module pages.  
4. Single `desktopStore` owns window + dock + icon state (no duplicated layout engine).  
5. Reuse shell icons, runtime health, notifications, workspace manager, dashboard profile.

## Files

### Added — `src/web/src/enterprise-desktop/`

- `types.ts`, `desktopCatalog.ts`, `desktopStore.ts`, `desktopStore.test.ts`  
- `DesktopShell.tsx`, `WindowFrame.tsx`, `EnterpriseDock.tsx`  
- `DesktopLauncher.tsx`, `DesktopIcons.tsx`, `useDesktopKeyboard.ts`  
- `enterprise-desktop.css`, `index.ts`

### Extended

| File | Change |
|------|--------|
| `App.tsx` | `/desktop` → `DesktopShell` |
| `layouts/WorkspaceLayout.tsx` | embed mode |
| `pages/SettingsPage.tsx` | embed mode + Desktop link |
| `shell/enterprise/enterpriseNav.ts` | Desktop nav item |
| `shell/enterprise/ShellIcons.tsx` | `desktop` icon |
| `config/webConfig.ts` | sprint `27.7` |
| `test/foundation.test.ts` | sprint assertion |
| `index.css` | desktop CSS import |
| `docs/DESKTOP.md` | Architecture guide |
| `docs/WINDOW_MANAGER.md` | Window manager guide |
| `docs/SPRINT_27_7_RESULT.md` | This report |

## Tests

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **97 passed** |
| build | OK |

## Remaining work before Enterprise City integration

- Deep `?embed=1` for all non-WorkspaceLayout surfaces (city, marketplace, twin, etc.)  
- Optional keep-alive window bodies (React portals) instead of iframe for shared auth/context  
- Multi-monitor / virtual desktop spaces  
- Enterprise City as first-class interactive desktop destination (beyond placeholder `/city` hub)  
- Host-level metrics in menubar (Observability API), not browser estimates  
- Folder windows with nested icon contents (currently folders open Documents)

## Verify

```bash
cd src/web && npm install && npm run lint && npm test && npm run build && npm run dev
```

Open `/desktop` · Cmd/Ctrl+Space · launch CRM · snap left · refresh → session restores.
