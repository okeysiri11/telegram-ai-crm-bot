# Enterprise Workflow Engine Architecture (Sprint OS 1.3)

## Diagram

```text
┌────────────┐
│   Kernel   │
└─────┬──────┘
      │
      ▼
┌────────────┐     ┌──────────────┐
│ Event Bus  │◄───►│ Service Mesh │
└─────┬──────┘     └──────┬───────┘
      │                   │
      └─────────┬─────────┘
                ▼
      ┌───────────────────┐
      │  Workflow Engine  │
      │  Def · Inst · Exe │
      └─────────┬─────────┘
                ▼
      Runtime → Agents → Business Modules
      (via handlers / mesh / events only)
```

## Example: Enterprise delivery

```text
User Request
    ↓
Enterprise Architect
    ↓
Backend Engineer
    ↓
  parallel.dev
   ├─ Database Engineer
   └─ Frontend Engineer
    ↓ (join)
QA → Docs → Knowledge → Approval → DevOps → Release
```

## Execution flow

```text
start(definitionId)
  → validate definition
  → create instance + context
  → executor.pump
       task | parallel | condition | approval | delay | event-wait
  → history append
  → Event Bus: WorkflowStarted / WorkflowFinished
```

## Rollback

Completed steps with `compensateWith` push onto a compensation stack.  
On failure (without `onError`), engine enters `Compensating` and runs compensations LIFO.

## Dependency direction

```text
workflow → (optional DI) event_bus / service_mesh interfaces
kernel → workflow
modules/plugins → register handlers / publish events  (never imported by workflow)
```
