# Workspace Manager

**Sprint:** 28.4 · Package: `src/web/src/enterprise-desktop/`

## Purpose

Save / restore Desktop workspace profiles and templates without a second storage engine.

## Persist

- Open windows (geometry, mode, tabs, z-order)
- Focused window
- Dock state
- Wallpaper / icon layout
- Active workspace profile id

## API (`useDesktopStore`)

| Action | Behavior |
|--------|----------|
| `saveWorkspaceProfile(name)` | Snapshot current desktop into named profile |
| `restoreWorkspaceProfile(id)` | Replace windows/dock/wallpaper from profile |
| `applyWorkspaceTemplate(id)` | blank · ops · creative · dev · executive |
| `listWorkspaceProfiles()` | Profiles in session |

## Templates

Defined in `workspaceProfiles.ts` — Creative opens AI Studio + Image + Video + Prompt simultaneously.

## Auto restore

`hydrate()` loads last session (v1 migrates to v2 with tabs/modes).

## Related

- [`WINDOW_MANAGER.md`](./WINDOW_MANAGER.md)
- [`SPRINT_28_4_RESULT.md`](./SPRINT_28_4_RESULT.md)
