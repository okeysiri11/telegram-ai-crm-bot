# Enterprise Event Bus Architecture (Sprint OS 1.1)

## Diagram

```text
┌────────────┐
│   Kernel   │
└─────┬──────┘
      │ BootCompleted / infrastructure
      ▼
┌─────────────────────────────────────────────┐
│           Enterprise Event Bus              │
│  Publisher → History → Dispatcher           │
│  Registry (types + sticky) · Subscriber     │
│  Filter · Mutex · Delayed timers            │
└─────┬───────────────┬───────────────┬───────┘
      │               │               │
      ▼               ▼               ▼
  Runtime          Agents      Business Modules
 (sessions)      (workers)    (CRM/ERP/… via events only)
```

## Communication rule

```text
Module A ──✕──► Module B     FORBIDDEN
Module A ──► Event Bus ──► Module B     REQUIRED
```

## Data flow (publish)

```text
publish(input)
  → Event.create
  → Registry.ensureKnown
  → [delayed] schedule timer
  → History.append (+ sticky)
  → Dispatcher → subscribers by priority
  → once cleanup
```

## Scalability

- History is a **ring buffer** (default capacity 100 000) — fixed memory, supports high publish rates
- Subscriber snapshots avoid mutation during dispatch
- Async mode uses microtask enqueue for throughput
- Delayed queue bounded by `maxDelayed`

## Dependency direction

```text
event_bus  (no deps on Runtime/Agents/Modules)
    ▲
kernel (BootLoader, KernelEventBusAdapter)
    ▲
runtime / plugins / business modules
```

## Plugin readiness

Plugins register custom event types on `EventRegistry` and subscribe via `IEnterpriseEventBus` — no Core changes.
