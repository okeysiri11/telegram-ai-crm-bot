# Sprint 28.7 — Enterprise Command Intelligence

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `28.7`  
**Constraint:** Extend Command Runtime only — no redesign.

## Implementation summary

Transformed Command Runtime into the platform execution engine:

1. **Undo / Redo** — `commandUndoStack` with groups + transactions  
2. **Macros** — record / stop / play / save / delete / rename / favorite  
3. **AI Intent Routing** — `routeAiIntent` / palette AI / `aiCommandCenter.execute`  
4. **Remote Policy** — user · org · workspace · device · remote_session  
5. **Launcher Registry** — Desktop launcher + shortcuts resolve registry IDs only  
6. **Analytics** — `commandIntelligenceAnalytics`  
7. **Inspector** — `/command-runtime` developer page  

## Architecture

```
AI Intent → commandRuntime.routeAiIntent
Launcher  → launcherRegistry → executeSync(commandId)
Palette   → execute / routeAiIntent
Desktop   → executeSync + Ctrl+Z/Shift+Z undo/redo
Shell     → executeCommand
```

## Modified / added (primary)

**New:** `commandUndoStack.ts`, `commandMacros.ts`, `commandPolicy.ts`, `commandIntelligenceAnalytics.ts`, `launcherRegistry.ts`, `aiIntentRouter.ts`, `CommandRuntimeInspectorPage.tsx`  

**Updated:** `commandRuntime.ts`, `commandTypes.ts`, `commandContext.ts`, `commandExecutor.ts`, `commandHistory.ts`, `index.ts`, `UniversalCommandPalette`, `aiCommands.ts`, `DesktopLauncher`, `useDesktopKeyboard`, `desktopCatalog`, `App.tsx`, `webConfig`  

**Docs:** `COMMAND_RUNTIME.md`, `COMMAND_MACROS.md`, `COMMAND_ANALYTICS.md`, `SPRINT_28_7_RESULT.md`, `ARCHITECTURE_MAP.md`

## Remaining work before Sprint 28.8

- Server-backed remote policy service  
- Cross-device undo sync  
- Macro marketplace / share  
- Visual macro editor  
- Full shortcut catalog bound to registry IDs  

## Tests / quality

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **201 passed** |
| build | OK |
