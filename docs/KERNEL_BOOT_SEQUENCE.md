# Enterprise Kernel Boot Sequence

**Sprint:** 29.9  
**Owner:** `KernelBootstrap` + `KernelLifecycle`

## Ordered steps

| # | Step ID | Action |
|---|---------|--------|
| 1 | `boot` | Enter boot phase |
| 2 | `configuration` | Load config · feature flags · license hooks |
| 3 | `runtime_registry` | Seed kernel registry (kernel + orchestrator + runtimes) |
| 4 | `dependency_validation` | Validate orchestrator dependency graph |
| 5 | `orchestrator_startup` | `enterpriseOrchestrator.startup()` |
| 6 | `all_runtime_startup` | Confirm runtimes registered/ready via orchestrator |
| 7 | `health_validation` | Aggregate health + EventBus smoke check |
| 8 | `platform_ready` | Seal boot clock · phase `ready` or `degraded` |

## Failure isolation

- Step failures are recorded on the boot timeline (`ok` / `failed` / `skipped`).
- Orchestrator or individual runtime failures mark the platform **degraded**, not crashed.
- License verification is a **non-blocking hook** (records result; does not halt boot in foundation mode).

## Shell integration

`enterpriseShellRuntime` calls `enterpriseKernel.boot()` after `commandRuntime.startup()`, replacing the prior direct `enterpriseOrchestrator.startup()` call. Orchestrator remains the ordered runtime coordinator under the Kernel.
