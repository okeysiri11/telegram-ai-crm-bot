# Sprint 28.4 — Enterprise Desktop Window Manager

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `28.4`  
**Constraint:** Extend Desktop only — no redesign of Runtime / AI Studio / Production.

## Implementation summary

Complete Window Manager on existing Enterprise Desktop:

- Modes: floating · snapped · maximized · fullscreen · minimized  
- Snap: edges · quarters · center · smart preview while dragging  
- Multi-edge resize · focus/z management · restore state machine  
- Window tabs (reorder/pin/duplicate/detach/merge) · split view  
- Multi-studio simultaneous windows (exact path identity)  
- Workspace profiles + templates + session v2 persistence  
- Shortcuts: Ctrl+Tab, Ctrl+W/N/D/Space, Ctrl+Shift+P, Alt+Tab, Esc, …  
- Developer Window Inspector  

## Architecture

```
DesktopShell
  ├── WindowFrame (chrome · tabs · iframe embed)
  ├── snap preview overlay
  ├── WindowInspector
  ├── Dock / Launcher
  └── useDesktopStore (single WM authority)
         └── ews_desktop_session_v1 (v2)
```

Reuses Event Bus, Notification Store, Workspace Manager IDs, AI Studio / Production routes as window content.

## Modified / added files (primary)

- `src/web/src/enterprise-desktop/types.ts`
- `src/web/src/enterprise-desktop/desktopStore.ts`
- `src/web/src/enterprise-desktop/WindowFrame.tsx`
- `src/web/src/enterprise-desktop/useDesktopKeyboard.ts`
- `src/web/src/enterprise-desktop/WindowInspector.tsx`
- `src/web/src/enterprise-desktop/workspaceProfiles.ts`
- `src/web/src/enterprise-desktop/shortcutCatalog.ts`
- `src/web/src/enterprise-desktop/DesktopShell.tsx`
- `src/web/src/enterprise-desktop/desktopCatalog.ts`
- `src/web/src/enterprise-desktop/enterprise-desktop.css`
- `docs/WINDOW_MANAGER.md` · `docs/WORKSPACE_MANAGER.md` · `docs/SPRINT_28_4_RESULT.md`

## Performance notes

- Lazy iframe `loading="lazy"`  
- Minimized windows unmounted (`return null`)  
- Snap preview is a single overlay node  
- Persist on mouse-up / discrete actions (not every mousemove)  
- Tab strip + split only when needed  

## Remaining work for Sprint 28.5

- True multi-monitor / dual-display window placement APIs  
- Browser Fullscreen API opt-in  
- Cross-window postMessage for iframe embeds  
- Dock multi-instance picker UI polish  
- Memory virtualization for >12 heavy studio iframes  
- Touch/pointer unified drag  

## Tests

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **184 passed** |
| build | OK |

## Readiness

| Area | Score |
|------|-------|
| Desktop Window Manager | **84%** |
| Enterprise Desktop | **88%** |
| Enterprise Platform | **82%** |
