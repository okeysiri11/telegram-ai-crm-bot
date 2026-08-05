# Command Macros

**Sprint:** 28.7  
**API:** `commandMacros` / `commandRuntime.macros`

## Lifecycle

```
record() → (commands execute & capture) → stop() → save(name)
play(id) · delete(id) · rename(id, name) · favorite(id)
```

## Storage

`localStorage` key `ews_cmd_macros_v1`

## Play

`commandRuntime.playMacro(id)` runs each step through `execute`, wrapped in an undo **group** so one Undo reverses the whole macro.

## Inspector

`/command-runtime` lists macros with Play · Record · Save controls.
