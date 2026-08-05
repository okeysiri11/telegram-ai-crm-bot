# Enterprise Kernel Diagnostics

**Sprint:** 29.9  
**Owner:** `KernelDiagnostics` + `KernelHealth`

## Collected signals

| Signal | Source |
|--------|--------|
| Runtime status | Orchestrator platform health / registry |
| Memory usage | `performance.memory` when available (browser) |
| Startup time | `KernelLifecycle.startupTimeMs()` |
| Failed modules | Boot steps + health unhealthy set |
| Dependency errors | Orchestrator dependency validation |
| Version mismatches | Kernel vs expected runtime versions |
| Configuration problems | Feature flags / license hook notes |
| EventBus health | Publish/subscribe smoke probe |

## Health aggregation

`KernelHealth.snapshot()` combines:

- Orchestrator `platformHealth`
- EventBus probe result
- Kernel phase (`ready` / `degraded` / …)

## Recovery linkage

Diagnostics feed recovery decisions: `KernelRecovery.recoverRuntime(id)` attempts graceful reload via orchestrator; on failure marks unhealthy, notifies orchestrator context, and continues platform operation.
