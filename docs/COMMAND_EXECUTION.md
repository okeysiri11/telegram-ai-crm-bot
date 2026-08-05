# Command Execution

**Sprint:** 28.6

## Execution flow

1. **Surface** sets context: `commandRuntime.setSurface("palette" | "shell" | "desktop")`
2. **Navigator** bound (SPA): `commandRuntime.bindNavigator(navigate)`
3. **Lookup** in `commandRegistry` by id or action
4. **Emit** `command.started` on Event Bus
5. **Authorize** via `meetsMinRole` + `canExecutePermission`
6. **Run** custom `handler` or `runDefaultHandler`
   - Shell/Palette: navigate to `route`
   - Desktop: `useDesktopStore.openApp` / window ops
7. **Record** `commandHistory` (+ palette recent bridge)
8. **Analytics** via existing `commandAnalytics`
9. **Emit** `command.completed` or `command.failed`
10. On success with route: also `enterpriseEventBus.openModule` for Shell recents

## Palette

`UniversalCommandPalette` → `commandRuntime.execute(...)`  
Legacy `actionExecutor.execute` is a thin sync wrapper over `commandRuntime.executeSync`.

## Shell

`enterpriseShellRuntime.startup()` calls `commandRuntime.startup()`.  
Quick actions: `executeShellQuickAction(id)` / `enterpriseShellRuntime.executeCommand`.

## Desktop

`DesktopShell` / `useDesktopKeyboard` set surface `desktop` and call `executeSync` for menubar opens and Ctrl+W / Ctrl+M window commands.

## Event types

Added to `EnterpriseEventType`:

- `command.started`
- `command.completed`
- `command.failed`
- `command.cancelled`

## Permissions

Roles: guest < client < operator < manager < developer < admin  

`ROLE_PERMISSIONS` maps baseline grants; `*` bypasses specific permission checks.
