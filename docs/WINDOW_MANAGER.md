# Window Manager

**Sprint:** 28.4 · Package: `src/web/src/enterprise-desktop/`

## Purpose

Enterprise Desktop Window Manager — multi-window OS chrome over existing Desktop runtime.

## Features

| Capability | Implementation |
|------------|----------------|
| Move / resize | `WindowFrame` + store `moveWindow` / `resizeWindow` (N/E/S/W/SE) |
| Maximize / minimize / restore | Mode-aware store transitions |
| Fullscreen | `setFullscreen` (desktop-canvas fullscreen, not browser FS API) |
| Floating / snapped / docked modes | `WindowMode` on `DesktopWindowState` |
| Snap | Left/Right/Top/Bottom + quarters + center + smart preview |
| Z-index / focus | Layered counters · highest-visible fallback |
| Tabs | Add · activate · reorder · pin · duplicate · reopen · detach · merge |
| Split view | Vertical / horizontal dual iframe |
| Multi-studio | Exact-path identity · `forceNew` |

## Authority

`useDesktopStore` is the only window lifecycle authority. Persistence key `ews_desktop_session_v1` snapshot **v2**.

## Related

- [`WORKSPACE_MANAGER.md`](./WORKSPACE_MANAGER.md)
- [`SPRINT_28_4_RESULT.md`](./SPRINT_28_4_RESULT.md)
