# Enterprise Kernel Runtime

**Sprint:** 29.9  
**Package:** `src/web/src/runtime/kernel`  
**Policy:** Orchestration-only — no business logic. Does **not** replace Orchestrator or City runtimes.

## Purpose

Platform bootstrap and lifecycle manager for the Enterprise Runtime ecosystem.

Responsibilities:

- Platform startup / shutdown / safe restart  
- Recovery after isolated runtime failure  
- Health aggregation  
- Version & configuration loading  
- Feature flags & license verification hooks  
- Platform diagnostics  

## Components

| Module | Role |
|--------|------|
| `EnterpriseKernel` | Facade · boot · shutdown · restart · recover |
| `KernelBootstrap` | Ordered boot sequence |
| `KernelConfiguration` | Config · feature flags · license hooks |
| `KernelLifecycle` | Phase machine · boot step tracking |
| `KernelRegistry` | Kernel view of platform modules |
| `KernelHealth` | Aggregated health + EventBus probe |
| `KernelDiagnostics` | Runtime status · memory · failures · mismatches |
| `KernelRecovery` | Per-runtime graceful restart · continue degraded |
| `KernelVersion` | Platform identity · version `29.9` |

## Lifecycle

```
Boot → Configuration → Runtime Registry → Dependency Validation
  → Orchestrator Startup → All Runtime Startup → Health Validation → Platform Ready
```

Kernel calls `enterpriseOrchestrator.startup()` for ordered runtime bring-up. Shell boots via `enterpriseKernel.boot()`.

## Recovery policy

If one runtime crashes: attempt graceful restart → if that fails, mark unhealthy, notify orchestrator, continue platform operation. Never crash the whole platform for one runtime.

## UI / API

- Dashboard: `/kernel`
- REST: `/api/enterprise-kernel/v1`
- EventBus: `kernel_runtime_update`
