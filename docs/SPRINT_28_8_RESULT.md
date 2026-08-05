# Sprint 28.8 — Enterprise Workflow Runtime

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `28.8`  
**Constraint:** One workflow engine on Command Runtime + Event Bus — no parallel runtimes.

## Implementation summary

- `workflowRuntime` facade: start · pause · resume · restart · cancel · approve · replay  
- Registry · sessions · history · execution engine with full node set  
- Seed from existing `BUSINESS_WORKFLOW_TEMPLATES` + demos  
- AI path: AI → Command Runtime → `start_workflow` → Workflow Runtime  
- EventBus `workflow_update` + wait_event bridge  
- Inspector at `/workflow-runtime`  
- Shell boots workflow runtime with command runtime  

## Architecture

```
Command Runtime ──► Workflow Runtime ──► EventBus / Notifications / Modules
                         │
                    Registry + Engine
```

## Modified / added (primary)

**New package:** `src/web/src/runtime/workflowRuntime/*`  
**Wired:** `enterpriseShellRuntime`, `App.tsx` route, launcher/desktop catalog, AI intent map  
**Docs:** `WORKFLOW_RUNTIME.md`, `WORKFLOW_ENGINE.md`, `WORKFLOW_INSPECTOR.md`, `SPRINT_28_8_RESULT.md`, Architecture Map  

## Remaining work before Sprint 28.9

- Visual graph editor tied to registry  
- Durable server-side workflow store  
- Join semantics for parallel branches  
- Webhook signature verification  
- Script sandbox runtime  

## Tests / quality

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **207 passed** |
| build | OK |
