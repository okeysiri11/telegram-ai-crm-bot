# Agent Communication

**Sprint:** 32.1 · `agentOs` message bus (in-memory, session-backed)

## Message types

`delegate` · `result` · `conflict` · `context` · `ping`

## Patterns

- Inter-agent messaging via `sendMessage` / `inbox`  
- Shared context via memory kinds `company` / `session` / `knowledge`  
- Task delegation + parallel workers in `runCollaborative`  
- Result aggregation + naive conflict detection  

**Not** a third product message bus — Python MAOS / platform_orchestrator buses remain backend; web SoR stays on Runtime.
