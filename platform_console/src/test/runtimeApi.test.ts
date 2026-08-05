import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { RUNTIME_HTTP, runtimeApi } from "../services/runtimeApi";

describe("runtimeApi", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        const path = String(url).replace(RUNTIME_HTTP, "");
        const bodies: Record<string, unknown> = {
          "/health": { status: "ok" },
          "/status": {
            version: "1.1.0",
            kernel: "OK",
            eventBus: "OK",
            serviceMesh: "OK",
            workflowEngine: "OK",
            runtimeServer: "OK",
            services: 2,
            systemStatus: "READY",
          },
        };
        return {
          ok: true,
          status: 200,
          json: async () => bodies[path] ?? {},
        };
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("connects to /health and /status", async () => {
    await expect(runtimeApi.health()).resolves.toEqual({ status: "ok" });
    const status = await runtimeApi.status();
    expect(status.systemStatus).toBe("READY");
    expect(status.kernel).toBe("OK");
    expect(fetch).toHaveBeenCalled();
  });
});

describe("WebSocket hook contract", () => {
  it("builds ws URL from runtime HTTP", async () => {
    const { RUNTIME_WS } = await import("../services/runtimeApi");
    expect(RUNTIME_WS).toContain("/ws");
    expect(RUNTIME_WS.startsWith("ws")).toBe(true);
  });
});
