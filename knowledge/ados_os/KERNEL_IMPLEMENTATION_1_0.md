---
title: ADOS Kernel Implementation 1.0
aliases:
  - Kernel Implementation
tags:
  - ados-os
  - kernel
  - implementation
status: active
---

# ADOS Kernel Implementation (Sprint OS 1.0)

## Location

Production TypeScript package: `src/kernel/` (`@ados/kernel`).

Knowledge design (prior): [[KERNEL]] · [[STARTUP_SEQUENCE]] · [[ADOS_OS]]

## Delivered components

| File | Role |
|------|------|
| `Kernel.ts` | Single entry; start/stop/dispose; BootCompleted |
| `BootLoader.ts` | Infrastructure boot sequence |
| `ServiceRegistry.ts` | register / unregister / resolve / exists / list |
| `Lifecycle.ts` | Created → … → Disposed |
| `HealthMonitor.ts` | Aggregates `health()` |

Interfaces live under `src/kernel/interfaces/`.

## Architecture rules (enforced)

- Kernel **does not** import business verticals.  
- Verticals depend on Kernel **interfaces**.  
- Plugin host + `IService` enable future plugins without Core edits.

See `src/kernel/docs/ARCHITECTURE.md` and `src/kernel/README.md`.

## Verify

```bash
cd src/kernel && npm install && npm test && npm run typecheck
```
