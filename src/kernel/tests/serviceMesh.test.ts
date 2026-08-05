import { describe, expect, it, beforeEach, afterEach } from "vitest";
import {
  createServiceMesh,
  ServiceMesh,
  ServiceDescriptor,
  isVersionCompatible,
  compareSemVer,
} from "../service_mesh/index.js";
import { createKernel } from "../Kernel.js";

describe("semver", () => {
  it("compares and checks ranges", () => {
    expect(compareSemVer("1.2.0", "1.1.9")).toBeGreaterThan(0);
    expect(isVersionCompatible("1.5.0", { min: "1.0.0", maxExclusive: "2.0.0" })).toBe(
      true,
    );
    expect(isVersionCompatible("2.0.0", { min: "1.0.0", maxExclusive: "2.0.0" })).toBe(
      false,
    );
    expect(isVersionCompatible("1.2.3", { exact: "1.2.3" })).toBe(true);
  });
});

describe("ServiceMesh", () => {
  let mesh: ServiceMesh;

  beforeEach(() => {
    mesh = createServiceMesh({ loadBalancer: "priority" });
  });

  afterEach(() => {
    mesh.dispose();
  });

  it("registers and discovers services", () => {
    mesh.register({
      id: "svc.a",
      version: "1.0.0",
      capabilities: ["chat", "embeddings"],
      tags: ["provider", "llm"],
      priority: 10,
    });
    mesh.register({
      id: "svc.b",
      version: "1.1.0",
      capabilities: ["chat"],
      tags: ["provider"],
      priority: 5,
    });

    const byCap = mesh.discover({ capability: "chat", healthyOnly: true });
    expect(byCap.map((s) => s.id)).toEqual(["svc.a", "svc.b"]);

    const byTag = mesh.discover({ tag: "llm" });
    expect(byTag).toHaveLength(1);
    expect(byTag[0]?.id).toBe("svc.a");
  });

  it("resolves dependencies and version compatibility", () => {
    mesh.register({
      id: "dep.store",
      version: "2.0.0",
      capabilities: ["storage"],
    });
    mesh.register({
      id: "app.worker",
      version: "1.0.0",
      capabilities: ["worker"],
      dependencies: [
        {
          capability: "storage",
          version: { min: "2.0.0", maxExclusive: "3.0.0" },
        },
        { serviceId: "missing.required", optional: false },
        { capability: "optional.cap", optional: true },
      ],
    });

    const result = mesh.resolver.resolveDependencies("app.worker");
    expect(result.ok).toBe(false);
    expect(result.resolved.some((s) => s.id === "dep.store")).toBe(true);
    expect(result.missing.some((d) => d.serviceId === "missing.required")).toBe(
      true,
    );
  });

  it("routes local calls with failover", async () => {
    let primaryCalls = 0;
    mesh.register({
      id: "api.primary",
      version: "1.0.0",
      capabilities: ["echo"],
      priority: 100,
      endpoints: [
        {
          id: "api.primary:local",
          capabilities: ["echo"],
          invoke: async () => {
            primaryCalls += 1;
            throw new Error("primary down");
          },
        },
      ],
    });
    mesh.register({
      id: "api.backup",
      version: "1.0.0",
      capabilities: ["echo"],
      priority: 10,
      endpoints: [
        {
          id: "api.backup:local",
          capabilities: ["echo"],
          invoke: async (_m, input) => ({ echoed: input }),
        },
      ],
    });

    const result = await mesh.route({
      capability: "echo",
      method: "echo",
      input: "hi",
    });
    expect(result.ok).toBe(true);
    expect(result.serviceId).toBe("api.backup");
    expect(result.data).toEqual({ echoed: "hi" });
    expect(result.failoverCount).toBeGreaterThanOrEqual(1);
    expect(primaryCalls).toBe(1);
  });

  it("enforces health monitoring and heartbeats", () => {
    mesh.register({
      id: "hb.svc",
      version: "1.0.0",
      capabilities: ["x"],
    });
    const hb = mesh.health.heartbeat("hb.svc", "healthy");
    expect(hb.status).toBe("healthy");
    expect(mesh.health.getStatus("hb.svc")).toBe("healthy");

    mesh.health.report("hb.svc", "degraded");
    expect(mesh.resolve("hb.svc").status).toBe("degraded");
  });

  it("applies version filters on discovery", () => {
    mesh.register({ id: "v1", version: "1.0.0", capabilities: ["api"] });
    mesh.register({ id: "v2", version: "2.0.0", capabilities: ["api"] });
    const onlyV2 = mesh.discover({
      capability: "api",
      version: { min: "2.0.0" },
    });
    expect(onlyV2.map((s) => s.id)).toEqual(["v2"]);
  });

  it("supports capability call helper", async () => {
    mesh.register({
      id: "math",
      version: "1.0.0",
      capabilities: ["math.add"],
      endpoints: [
        {
          id: "math:local",
          capabilities: ["math.add"],
          invoke: async (_m, input) => {
            const n = input as { a: number; b: number };
            return n.a + n.b;
          },
        },
      ],
    });
    const result = await mesh.call("math.add", "add", { a: 2, b: 3 });
    expect(result.ok).toBe(true);
    expect(result.data).toBe(5);
  });

  it("rejects invalid descriptors", () => {
    expect(() => ServiceDescriptor.create({ id: "", version: "1" })).toThrow();
  });
});

describe("Kernel + Service Mesh", () => {
  it("auto-registers boot services into the mesh", async () => {
    const kernel = createKernel({ config: { environment: "test" } });
    await kernel.start();
    expect(kernel.version).toBe("1.4.0");
    expect(kernel.serviceMesh.stats().services).toBeGreaterThanOrEqual(5);
    expect(kernel.serviceMesh.discovery.get("ados.event_bus")).toBeTruthy();

    const healthCall = await kernel.serviceMesh.callLocal(
      "ados.provider_host",
      "health",
    );
    // callLocal uses service id routing
    const viaRoute = await kernel.serviceMesh.route({
      serviceId: "ados.provider_host",
      method: "health",
    });
    expect(viaRoute.ok).toBe(true);
    expect(healthCall.ok).toBe(true);
    await kernel.dispose();
  });
});
