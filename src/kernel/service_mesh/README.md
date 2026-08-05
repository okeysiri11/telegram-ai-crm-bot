# ADOS Enterprise Service Mesh (Sprint OS 1.2)

## Purpose

The **Service Mesh** is the discovery and communication layer for every internal ADOS service.

```text
Kernel
  ↓
Service Registry
  ↓
Service Mesh
  ↓
Runtime → Modules → Providers → Plugins
```

Modules **do not** call each other directly — they discover and route through the mesh (and coordinate via the Event Bus).

## Location

`src/kernel/service_mesh/`

| File | Role |
|------|------|
| `ServiceMesh.ts` | Facade |
| `ServiceDescriptor.ts` | Registration record |
| `ServiceEndpoint.ts` | Local / remote-ready endpoints |
| `ServiceDiscovery.ts` | Register + query |
| `ServiceResolver.ts` | Dependencies + semver |
| `ServiceHealth.ts` | Heartbeats + status |
| `ServiceRouter.ts` | Route + failover |
| `ServicePolicy.ts` | Allow/deny |
| `LoadBalancer.ts` | Priority / RR / random |

## Quick start

```ts
import { createServiceMesh, createKernel } from "@ados/kernel";

const mesh = createServiceMesh({ loadBalancer: "priority" });

mesh.register({
  id: "provider.chat",
  version: "1.0.0",
  capabilities: ["chat"],
  tags: ["provider"],
  priority: 10,
  endpoints: [
    {
      id: "provider.chat:local",
      capabilities: ["chat"],
      invoke: async (method, input) => ({ method, input }),
    },
  ],
});

const result = await mesh.route({
  capability: "chat",
  method: "complete",
  input: { prompt: "hello" },
});
```

Kernel boot auto-registers lifecycle services into `kernel.serviceMesh`.

## Capabilities

- Automatic registration & discovery (id, capability, tags, version, health)
- Dependency resolution + semver compatibility
- Health reporting & heartbeat monitoring
- Routing with load balancing and failover
- Local invokes; http/grpc endpoints reserved for future cluster
- Policies, priority, plugin/provider ready
- DI via `IServiceMesh`, `IServiceDiscovery`, `IServiceResolver`, `IServiceHealth`, `IServiceRouter`

## Architecture rules

- No business-module imports
- Kernel owns the mesh
- No circular dependencies
- Plugin/provider register descriptors only

## Verify

```bash
cd src/kernel && npm test && npm run typecheck
```

See `../docs/SERVICE_MESH_ARCHITECTURE.md`.
