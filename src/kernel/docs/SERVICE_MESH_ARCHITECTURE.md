# Enterprise Service Mesh Architecture (Sprint OS 1.2)

## Diagram

```text
┌──────────────────────────────────────────┐
│                 Kernel                   │
│   ServiceRegistry · EventBus · Mesh      │
└───────────────────┬──────────────────────┘
                    │ owns
                    ▼
┌──────────────────────────────────────────┐
│            Service Mesh                  │
│  Discovery → Resolver → Health → Router  │
│  Policy · LoadBalancer · Descriptors     │
└───────┬──────────┬──────────┬────────────┘
        ▼          ▼          ▼
    Runtime     Modules    Providers/Plugins
```

## Communication rule

```text
Module A ──✕──► Module B              FORBIDDEN
Module A ──► Service Mesh.route() ──► Module B endpoint   REQUIRED
Module A ──► Event Bus.publish() ──► Module B subscriber  (async facts)
```

## Registration flow

```text
Boot / Plugin load
  → ServiceRegistry.register(IService)
  → descriptorFromKernelService / ServiceDescriptor.create
  → ServiceMesh.register
  → Health.watch + heartbeat
```

## Routing flow

```text
route({ capability, method, input, version? })
  → Discovery.discover (healthy + version + tags)
  → Policy.filterAllowed
  → LoadBalancer.select
  → Endpoint.invoke
  → on failure: failover chain
```

## Future cluster

- `nodeId` on descriptors
- `protocol: http | grpc` endpoints (remote-ready; unbound locally)
- `preferNodeId` on route requests

## Dependency direction

```text
service_mesh  (minimal; may adapt kernel IService)
     ▲
  Kernel
     ▲
 Runtime / Plugins / Modules
```

No imports of CRM, ERP, Marketplace, or other verticals.
