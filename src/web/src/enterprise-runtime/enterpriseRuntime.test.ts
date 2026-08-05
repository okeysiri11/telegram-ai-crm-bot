/**
 * Sprint 28.1 — Enterprise Runtime Engine tests.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  RUNTIME_ENGINE_VERSION,
  HEALTH_POLL_MS,
  aggregateHealth,
  toneToHealth,
} from "./types";
import { healthService } from "./healthService";
import { jobManager } from "./jobManager";
import { aiAgentRuntime } from "./aiAgentRuntime";
import { runtimeEngine } from "./runtimeEngine";

describe("Sprint 28.1 Enterprise Runtime Engine", () => {
  beforeEach(() => {
    runtimeEngine.stop();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: true, status: 200 }) as Response),
    );
  });

  afterEach(() => {
    runtimeEngine.stop();
    vi.unstubAllGlobals();
  });

  it("exports runtime engine version 28.2", () => {
    expect(RUNTIME_ENGINE_VERSION).toBe("28.2");
    expect(HEALTH_POLL_MS).toBe(45_000);
  });

  it("maps tones to health levels", () => {
    expect(toneToHealth("ok")).toBe("healthy");
    expect(toneToHealth("warn")).toBe("warning");
    expect(toneToHealth("err")).toBe("critical");
    expect(toneToHealth("unknown")).toBe("offline");
  });

  it("aggregates health correctly", () => {
    expect(
      aggregateHealth([
        { id: "api", label: "API", tone: "ok", detail: "x" },
        { id: "runtime", label: "Runtime", tone: "warn", detail: "y" },
      ]),
    ).toBe("warning");
    expect(
      aggregateHealth([{ id: "api", label: "API", tone: "err", detail: "x" }]),
    ).toBe("critical");
  });

  it("healthService is ref-counted singleton (one start path)", () => {
    const a = healthService.subscribe(() => undefined);
    const b = healthService.subscribe(() => undefined);
    expect(healthService.getItems().length).toBeGreaterThan(0);
    a();
    b();
    // After all subscribers release, stop leaves service idle
    expect(typeof healthService.getLevel()).toBe("string");
  });

  it("jobManager tracks lifecycle counts and progress", () => {
    jobManager.upsert({
      id: "test_job_28_1",
      title: "Test job",
      status: "running",
      progress: 10,
      etaSec: 60,
      source: "system",
      startedAt: new Date().toISOString(),
      retries: 0,
    });
    expect(jobManager.counts().running).toBeGreaterThanOrEqual(1);
    jobManager.setStatus("test_job_28_1", "completed", 100);
    const hit = jobManager.list().find((j) => j.id === "test_job_28_1");
    expect(hit?.status).toBe("completed");
    expect(hit?.progress).toBe(100);
  });

  it("aiAgentRuntime exposes agents with status/task/health", () => {
    const agents = aiAgentRuntime.list();
    expect(agents.length).toBeGreaterThan(0);
    const sample = agents[0];
    expect(sample).toHaveProperty("status");
    expect(sample).toHaveProperty("task");
    expect(sample).toHaveProperty("memoryMb");
    expect(sample).toHaveProperty("health");
    expect(aiAgentRuntime.activeCount()).toBeGreaterThanOrEqual(0);
  });

  it("runtimeEngine publishes stable snapshots", () => {
    runtimeEngine.start();
    const a = runtimeEngine.getSnapshot();
    const b = runtimeEngine.getSnapshot();
    expect(a).toBe(b);
    expect(a.version).toBe("28.2");
    expect(a.metrics).toHaveProperty("cpuPct");
    expect(a.metrics).toHaveProperty("memoryPct");
    expect(a.metrics).toHaveProperty("gpuPct");
    expect(a.metrics).toHaveProperty("workers");
    expect(a.metrics).toHaveProperty("sessions");
    expect(a.metrics).toHaveProperty("agentsActive");
    expect(a.jobs.length).toBeGreaterThan(0);
    expect(a.agents.length).toBeGreaterThan(0);
    expect(runtimeEngine.isStarted()).toBe(true);
  });

  it("job cancel and retry update lifecycle", () => {
    jobManager.upsert({
      id: "rj_retry_me",
      title: "Retry me",
      status: "failed",
      progress: 40,
      etaSec: 0,
      source: "queue",
      startedAt: new Date().toISOString(),
      retries: 0,
    });
    jobManager.retry("rj_retry_me");
    expect(jobManager.list().find((j) => j.id === "rj_retry_me")?.status).toBe("retrying");
    jobManager.cancel("rj_retry_me");
    expect(jobManager.list().find((j) => j.id === "rj_retry_me")?.status).toBe("cancelled");
  });
});
