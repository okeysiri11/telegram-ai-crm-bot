# ADOS OS 1.0 — Enterprise Kernel

## Purpose

Production TypeScript implementation of the **ADOS Kernel**: single entry point that boots infrastructure, registers services, monitors health, and publishes `BootCompleted`.

**Architecture invariant:** the Kernel never depends on business modules (CRM, ERP, Marketplace, AI Studio, or other verticals). Business modules and plugins depend on the Kernel via interfaces.

## Package layout

```text
src/kernel/
  Kernel.ts              Single entry point
  BootLoader.ts          Infrastructure boot sequence
  ServiceRegistry.ts     DI-ready register/resolve
  Lifecycle.ts           Created → … → Disposed
  HealthMonitor.ts       Aggregates service health()
  interfaces/            Public contracts
  infra/                 Infrastructure hosts (not verticals)
  events/                Kernel event bus
  config/                Kernel configuration
  tests/                 Unit tests
  docs/ARCHITECTURE.md   Diagram & rules
```

## Quick start

```bash
cd src/kernel
npm install
npm test
npm run typecheck
```

```ts
import { createKernel } from "@ados/kernel";

const kernel = createKernel({ config: { environment: "development" } });
kernel.eventBus.subscribe("BootCompleted", (e) => {
  console.log("ADOS ready", e.serviceIds);
});
await kernel.start();
const health = await kernel.getHealth();
await kernel.stop();
await kernel.dispose();
```

## Boot sequence

```text
load-config
  → register-services (event bus, provider/runtime/memory/plugin hosts)
  → initialize-providers
  → initialize-runtime
  → initialize-memory
  → initialize-plugins
  → start-services
  → BootCompleted event
```

## Service contract

Every service exposes: `id`, `version`, `kind`, lifecycle, `uptimeMs()`, `health()`, and lifecycle methods (`initialize` / `start` / `pause` / `stop` / `dispose`).

## Extensibility

Future plugins register additional `IService` implementations on `ServiceRegistry` and optionally record ids on `PluginHostService` — **without modifying Kernel internals or Core**.

## Related knowledge

- `knowledge/ados_os/KERNEL.md`
- `knowledge/ados_os/STARTUP_SEQUENCE.md`
- `knowledge/sdk/SDK_OVERVIEW.md`
