# Command Runtime

**Sprint:** 28.7  
**Package:** `src/web/src/runtime/commandRuntime/`  
**Version:** `COMMAND_RUNTIME_VERSION = "28.7"`

## Role

Central **Enterprise Command Execution Engine** for Palette, Shell, Desktop, AI intents, macros, and undo/redo. No platform action should bypass this runtime.

## Architecture

```
AI / Palette / Shell / Desktop / Launcher / Shortcuts
                    │
                    ▼
            commandRuntime
       ┌────────────┼────────────┐
       ▼            ▼            ▼
  Registry     Permissions    Policy
       │            │            │
       └────────────┼────────────┘
                    ▼
              commandExecutor
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
  Undo stack    History      Analytics
  Macros        EventBus     Inspector
```

## Public API

```ts
commandRuntime.execute / executeSync
commandRuntime.undo / redo
commandRuntime.beginGroup / endGroup
commandRuntime.beginTransaction / commitTransaction / rollbackTransaction
commandRuntime.macros.record|stop|save|play|delete|rename|favorite
commandRuntime.routeAiIntent(utterance)
commandRuntime.launcher.resolveCommandId(appId)
commandRuntime.policy.setScope(...)
commandRuntime.analytics()
commandRuntime.inspectorSnapshot()
```

## Surfaces

| Surface | Integration |
|---------|-------------|
| Palette | `commandRuntime.execute` · AI → `routeAiIntent` |
| Shell | `enterpriseShellRuntime.executeCommand` |
| Desktop | Launcher + menubar + Ctrl+Z/Y window ops |
| Inspector | `/command-runtime` |

## Related

- [`COMMAND_EXECUTION.md`](./COMMAND_EXECUTION.md)
- [`COMMAND_MACROS.md`](./COMMAND_MACROS.md)
- [`COMMAND_ANALYTICS.md`](./COMMAND_ANALYTICS.md)
- [`SPRINT_28_7_RESULT.md`](./SPRINT_28_7_RESULT.md)
