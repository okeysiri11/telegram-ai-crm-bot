---
title: ADOS Enterprise Service Mesh Implementation 1.2
aliases:
  - Service Mesh Implementation
tags:
  - ados-os
  - service-mesh
  - implementation
status: active
---

# ADOS Enterprise Service Mesh (Sprint OS 1.2)

## Location

`src/kernel/service_mesh/` — production TypeScript (`@ados/kernel` **1.2.0**).

Prior design: [[../ados_os/SERVICE_REGISTRY|SERVICE_REGISTRY]] · Kernel: [[KERNEL_IMPLEMENTATION_1_0]] · Event Bus: [[EVENT_BUS_IMPLEMENTATION_1_1]]

## Backbone

```text
Kernel → Service Registry → Service Mesh → Runtime → Modules → Providers → Plugins
```

## Interfaces

`IServiceMesh` · `IServiceDiscovery` · `IServiceResolver` · `IServiceHealth` · `IServiceRouter`  
(+ kernel lifecycle `IService` bridged via `descriptorFromKernelService`)

## Verify

```bash
cd src/kernel && npm test && npm run typecheck && npm run build
```

README: `src/kernel/service_mesh/README.md`  
Architecture: `src/kernel/docs/SERVICE_MESH_ARCHITECTURE.md`
