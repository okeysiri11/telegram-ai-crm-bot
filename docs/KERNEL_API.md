# Enterprise Kernel API

**Sprint:** 29.9  
**Prefix:** `/api/enterprise-kernel/v1`  
**Client:** `src/web/src/runtime/kernel/kernelApi.ts`  
**Vite plugin:** `src/web/vite.kernelApiPlugin.ts`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health probe |
| GET | `/status` | Platform phase · ready · degraded |
| GET | `/diagnostics` | Latest diagnostic report |
| GET | `/boot-sequence` | Boot step timeline |
| GET | `/modules` | Registered kernel modules |
| GET | `/recovery` | Recovery history |
| GET | `/config` | Feature flags · license hooks |
| GET | `/inventory` | Endpoint inventory |

## Local fallback

When remote Vite middleware returns stubs or is unavailable, `kernelApi` falls back to in-process `enterpriseKernel` methods (`local_engine` mode).

## EventBus

Type: `kernel_runtime_update`  
Payload examples: `BootCompleted`, `DiagnosticsCollected`, `RecoveryAttempted`, `HealthProbe`.
