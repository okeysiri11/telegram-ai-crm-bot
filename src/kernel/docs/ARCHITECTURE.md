# ADOS Kernel Architecture (Sprint OS 1.0)

## Diagram

```text
                    ┌─────────────────────────┐
                    │     createKernel()      │
                    │      Kernel.start       │
                    └───────────┬─────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────┐
│                         Kernel                            │
│  config · Lifecycle · EventBus · HealthMonitor · Registry │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│                       BootLoader                          │
│  load-config → register → providers → runtime → memory    │
│              → plugins → start-services → boot-completed  │
└───────────────────────────┬───────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   ServiceRegistry    HealthMonitor      EventBus
   register/resolve   health() aggregate BootCompleted
          │
          ▼
┌───────────────────────────────────────────────────────────┐
│              Infrastructure services (hosts)              │
│  ados.event_bus · ados.provider_host · ados.runtime_host  │
│  ados.memory_host · ados.plugin_host · (+ future plugins) │
└───────────────────────────────────────────────────────────┘
                            △
                            │ depends on interfaces only
                            │
          ┌─────────────────┴─────────────────┐
          │   Business modules / Plugins      │
          │   CRM · ERP · Marketplace · …     │
          │   (NEVER imported by Kernel)      │
          └───────────────────────────────────┘
```

## Dependency rules

| From | To | Allowed |
|------|-----|---------|
| Kernel | Infrastructure interfaces / hosts | Yes |
| Kernel | CRM / ERP / Marketplace / AI Studio | **No** |
| Business module | `IKernel`, `IServiceRegistry`, SDK | Yes |
| Plugin | `IService` + register on Registry | Yes |
| Host A | Host B via Registry.resolve | Yes (no circular construct imports) |

## Lifecycle

```text
Created → Initialized → Started ⇄ Paused → Stopped → Disposed
```

## Health

Each service: `id`, `status`, `uptimeMs`, `version`, `health()`.  
`HealthMonitor.report()` aggregates platform status (`healthy` / `degraded` / `unhealthy` / …).

## Plugin readiness

- `ados.plugin_host` started during boot  
- Extra `IService` with `kind: "extension"` can register post-boot  
- Manifests/SDK (knowledge/sdk) bind later without Kernel redesign  

## No circular dependencies

Construction order: `Lifecycle` / `ServiceRegistry` / `HealthMonitor` / `EventBus` → `BootLoader` → `Kernel`.  
Hosts depend only on `InfrastructureService` + interfaces — not on `Kernel`.
