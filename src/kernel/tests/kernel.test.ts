import { describe, expect, it, beforeEach } from "vitest";
import { createKernel, Kernel } from "../Kernel.js";
import { Lifecycle } from "../Lifecycle.js";
import {
  ServiceAlreadyRegisteredError,
  ServiceNotFoundError,
  ServiceRegistry,
} from "../ServiceRegistry.js";
import { HealthMonitor } from "../HealthMonitor.js";
import { BootLoader } from "../BootLoader.js";
import { InfrastructureService } from "../infra/InfrastructureService.js";
import {
  EVENT_BUS_SERVICE_ID,
  MEMORY_HOST_SERVICE_ID,
  PLUGIN_HOST_SERVICE_ID,
  PROVIDER_HOST_SERVICE_ID,
  RUNTIME_HOST_SERVICE_ID,
} from "../index.js";
import type { BootCompletedPayload } from "../interfaces/types.js";

describe("Lifecycle", () => {
  it("allows the full happy path", () => {
    const life = new Lifecycle();
    expect(life.state).toBe("Created");
    life.transition("Initialized");
    life.transition("Started");
    life.transition("Paused");
    life.transition("Started");
    life.transition("Stopped");
    life.transition("Disposed");
    expect(life.state).toBe("Disposed");
  });

  it("rejects illegal transitions", () => {
    const life = new Lifecycle();
    expect(() => life.transition("Started")).toThrow(/Invalid lifecycle/);
  });

  it("notifies listeners", () => {
    const life = new Lifecycle();
    const seen: string[] = [];
    life.onTransition((from, to) => seen.push(`${from}->${to}`));
    life.transition("Initialized");
    expect(seen).toEqual(["Created->Initialized"]);
  });
});

describe("ServiceRegistry", () => {
  let registry: ServiceRegistry;

  beforeEach(() => {
    registry = new ServiceRegistry();
  });

  it("register / resolve / exists / list / unregister", () => {
    const svc = new InfrastructureService({
      id: "ados.test",
      kind: "infrastructure",
    });
    registry.register(svc);
    expect(registry.exists("ados.test")).toBe(true);
    expect(registry.resolve("ados.test")).toBe(svc);
    expect(registry.list()).toHaveLength(1);
    expect(registry.unregister("ados.test")).toBe(true);
    expect(registry.exists("ados.test")).toBe(false);
  });

  it("throws when resolving missing service", () => {
    expect(() => registry.resolve("missing")).toThrow(ServiceNotFoundError);
  });

  it("throws on duplicate unless replace", () => {
    const a = new InfrastructureService({
      id: "ados.dup",
      kind: "infrastructure",
      version: "1.0.0",
    });
    const b = new InfrastructureService({
      id: "ados.dup",
      kind: "infrastructure",
      version: "2.0.0",
    });
    registry.register(a);
    expect(() => registry.register(b)).toThrow(ServiceAlreadyRegisteredError);
    registry.register(b, { replace: true });
    expect(registry.resolve("ados.dup").version).toBe("2.0.0");
  });
});

describe("HealthMonitor", () => {
  it("aggregates service health", async () => {
    const monitor = new HealthMonitor();
    const a = new InfrastructureService({
      id: "a",
      kind: "infrastructure",
    });
    const b = new InfrastructureService({
      id: "b",
      kind: "infrastructure",
    });
    await a.initialize();
    await a.start();
    await b.initialize();
    await b.start();
    b.setForcedStatus("degraded");

    monitor.watch(a);
    monitor.watch(b);
    const report = await monitor.report();
    expect(report.services).toHaveLength(2);
    expect(report.healthyCount).toBe(1);
    expect(report.degradedCount).toBe(1);
    expect(report.status).toBe("degraded");
  });
});

describe("BootLoader", () => {
  it("completes infrastructure phases without business modules", async () => {
    const loader = new BootLoader();
    const registry = new ServiceRegistry();
    await loader.boot({
      registry,
      config: {
        edition: "enterprise",
        environment: "test",
        version: "1.0.0",
        failFast: true,
        featureFlags: {
          plugins: true,
          providers: true,
          runtime: true,
          memory: true,
        },
      },
    });

    expect(loader.phasesCompleted).toEqual([
      "load-config",
      "register-services",
      "initialize-providers",
      "initialize-runtime",
      "initialize-memory",
      "initialize-plugins",
      "start-services",
      "boot-completed",
    ]);

    for (const id of [
      EVENT_BUS_SERVICE_ID,
      PROVIDER_HOST_SERVICE_ID,
      RUNTIME_HOST_SERVICE_ID,
      MEMORY_HOST_SERVICE_ID,
      PLUGIN_HOST_SERVICE_ID,
    ]) {
      expect(registry.exists(id)).toBe(true);
      expect(registry.resolve(id).getLifecycleState()).toBe("Started");
    }
  });
});

describe("Kernel", () => {
  let kernel: Kernel;

  beforeEach(() => {
    kernel = createKernel({
      config: { environment: "test", failFast: true },
    });
  });

  it("starts successfully and publishes BootCompleted", async () => {
    let bootEvent: BootCompletedPayload | undefined;
    kernel.eventBus.subscribe("BootCompleted", (payload) => {
      bootEvent = payload;
    });

    await kernel.start();

    expect(kernel.getState()).toBe("Started");
    expect(bootEvent?.kernelVersion).toBe("1.4.0");
    expect(bootEvent?.serviceIds.length).toBeGreaterThanOrEqual(5);
    expect(kernel.registry.exists(PROVIDER_HOST_SERVICE_ID)).toBe(true);
  });

  it("registers services and reports health for all", async () => {
    await kernel.start();
    const health = await kernel.getHealth();
    expect(health.services.length).toBe(kernel.registry.list().length);
    expect(health.healthyCount).toBe(health.services.length);
    expect(health.status).toBe("healthy");
  });

  it("supports pause / resume / stop / dispose lifecycle", async () => {
    await kernel.start();
    await kernel.pause();
    expect(kernel.getState()).toBe("Paused");
    await kernel.resume();
    expect(kernel.getState()).toBe("Started");
    await kernel.stop();
    expect(kernel.getState()).toBe("Stopped");
    await kernel.dispose();
    expect(kernel.getState()).toBe("Disposed");
  });

  it("accepts future plugin host registration without Core changes", async () => {
    await kernel.start();
    const extension = new InfrastructureService({
      id: "plugin.sample.extension",
      kind: "extension",
      version: "0.1.0",
      critical: false,
    });
    await extension.initialize();
    await extension.start();
    kernel.registry.register(extension);
    kernel.healthMonitor.watch(extension);

    const health = await kernel.getHealth();
    expect(health.services.some((s) => s.id === "plugin.sample.extension")).toBe(
      true,
    );
  });

  it("does not import or reference business vertical service ids", async () => {
    await kernel.start();
    const ids = kernel.registry.list().map((s) => s.id);
    for (const banned of ["crm", "erp", "marketplace", "ai-studio", "ai_studio"]) {
      expect(ids.some((id) => id.toLowerCase().includes(banned))).toBe(false);
    }
  });
});
