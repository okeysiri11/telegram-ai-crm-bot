# Enterprise Desktop Environment

**Sprint:** 27.7  
**App:** `src/web`  
**Package:** `src/enterprise-desktop/`  
**Route:** `/desktop`

## Purpose

Provide a real **Enterprise Desktop** experience — canvas, wallpaper, icons, dock, windowed modules, launcher, and workspace memory — without redesigning existing apps. Modules open inside windows via same-origin `?embed=1` iframes.

## Architecture

```
/desktop → DesktopShell
            ├── desktopStore (ews_desktop_session_v1)
            ├── DesktopMenubar (status · wallpaper · layout)
            ├── Desktop canvas
            │     ├── DesktopIcons (drag · folders · shortcuts)
            │     └── WindowFrame[] (move · resize · snap · iframe embed)
            ├── DesktopLauncher (Cmd/Ctrl+Space)
            └── EnterpriseDock (pinned · running · badges)
```

**Extend only:** reuses shell icons, `useRuntimeHealth`, notification store, Command Center palette, workspace manager, live dashboard profile, EDL motion tokens. Does not replace FullLayout / tabs for classic routes.

## Surfaces

| Surface | Behavior |
|---------|----------|
| Canvas | Wallpaper backgrounds, icon grid per layout profile |
| Icons | Apps, folders, shortcuts; drag positions persist |
| Dock | Pinned + running + recent; hover scale; badges; minimize/restore |
| Launcher | CRM · ERP · Finance · Knowledge · AI Studio · Marketplace · Analytics · Settings · City · Production · DevTools |
| Windows | See [WINDOW_MANAGER.md](./WINDOW_MANAGER.md) |

## Workspace memory

Persisted under `ews_desktop_session_v1`:

- Open windows + geometry  
- Desktop layout + icon positions  
- Dock pins / recent apps  
- Wallpaper  
- Selected dashboard profile + active workspace id  

## Keyboard

| Shortcut | Action |
|----------|--------|
| Alt+Tab | Cycle windows |
| Cmd/Ctrl+Space | Launcher |
| Esc | Close launcher |
| Cmd/Ctrl+W | Close focused window |
| Cmd/Ctrl+Shift+T | Reopen closed |
| Cmd/Ctrl+K | Command palette |

## Status integration

Menubar / dock react to notifications, AI health, provider health, runtime health, and background jobs (via existing stores/pollers).

## Enterprise City (Sprint 27.8)

City is the **primary navigation space** on top of Desktop OS:

- Dock pin **Enterprise City** → `/enterprise-city?embed=1`
- Menubar link · shell nav · `/city` alias
- Buildings open existing routes inside Desktop windows

See [ENTERPRISE_CITY_CORE.md](./ENTERPRISE_CITY_CORE.md).

## AI Production Center (Sprint 27.9)

Desktop apps **Production Studio / Reels / Ads / Prompt Studio** open `/production-studio` (embed-ready). City Production District buildings deep-link into studios.

See [AI_PRODUCTION_CENTER_ARCHITECTURE.md](./AI_PRODUCTION_CENTER_ARCHITECTURE.md).

## Integration Hub (Sprint 28.0)

Shared context · event bus · session restore · universal search · deep links across Desktop / City / Production / Dashboard.

See [INTEGRATION_HUB.md](./INTEGRATION_HUB.md).

## Performance

- Lazy iframe `loading="lazy"`  
- Minimized windows not mounted  
- Zustand selectors are field-scoped  
- Single persistence key — no duplicated window state outside `desktopStore`

## Verify

```bash
cd src/web && npm run lint && npm test && npm run build && npm run dev
```

Open `/desktop` · launcher · open CRM · snap left · refresh (session restores).
