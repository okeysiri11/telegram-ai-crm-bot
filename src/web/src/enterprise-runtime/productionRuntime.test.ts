/**
 * Sprint 28.2 — Production Runtime tests.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { RUNTIME_ENGINE_VERSION } from "./types";
import { jobManager } from "./jobManager";
import { productionRuntime } from "./productionRuntime";
import { UNIVERSAL_PIPELINES, universalPipelineById } from "./universalPipelines";
import { runtimeEngine } from "./runtimeEngine";

describe("Sprint 28.2 AI Production Center Runtime", () => {
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

  it("bumps runtime engine to 28.2", () => {
    expect(RUNTIME_ENGINE_VERSION).toBe("28.2");
  });

  it("exposes five production queues", () => {
    expect(productionRuntime.queues()).toEqual([
      "production",
      "task",
      "render",
      "generation",
      "publishing",
    ]);
  });

  it("defines eight universal pipelines", () => {
    expect(UNIVERSAL_PIPELINES).toHaveLength(8);
    expect(universalPipelineById("reels_generation")?.collaboration).toBe("multi");
    expect(universalPipelineById("publishing")?.primaryQueue).toBe("publishing");
  });

  it("enqueues through Job Manager with queue metadata", () => {
    const id = productionRuntime.enqueue({
      title: "Unit gen job",
      queueKind: "generation",
      studioId: "image",
      agents: ["Creative Director"],
    });
    const hit = jobManager.list().find((j) => j.id === id);
    expect(hit?.queueKind).toBe("generation");
    expect(hit?.source).toBe("production");
    expect(hit?.status).toBe("waiting");
  });

  it("runs universal pipeline into multiple queue lanes", () => {
    const { jobIds, pipeline } = productionRuntime.runUniversalPipeline("reels_generation", {
      title: "Test reel",
    });
    expect(pipeline.id).toBe("reels_generation");
    expect(jobIds.length).toBeGreaterThanOrEqual(2);
    const queued = jobManager.list().filter((j) => jobIds.includes(j.id));
    expect(queued.some((j) => j.queueKind === "task")).toBe(true);
    expect(queued.some((j) => j.queueKind === "generation" || j.queueKind === "production")).toBe(true);
  });

  it("workers schedule waiting jobs on tick", () => {
    productionRuntime.enqueue({
      title: "Tick render",
      queueKind: "render",
      studioId: "render",
    });
    productionRuntime.tick();
    const renderJobs = productionRuntime.listQueue("render");
    expect(renderJobs.some((j) => j.status === "running" || j.status === "waiting")).toBe(true);
    expect(productionRuntime.workers().length).toBeGreaterThanOrEqual(5);
    const analytics = productionRuntime.analytics();
    expect(analytics.byQueue.render).toBeDefined();
  });

  it("retry manager flips failed jobs", () => {
    const id = productionRuntime.enqueue({
      title: "Will fail",
      queueKind: "task",
      status: "waiting",
    });
    jobManager.setStatus(id, "failed", 40);
    const retried = productionRuntime.retryFailed(5);
    expect(retried).toContain(id);
    expect(jobManager.list().find((j) => j.id === id)?.status).toBe("retrying");
  });

  it("monitor exposes queue lengths and workers", () => {
    const mon = productionRuntime.monitor();
    expect(mon.queues.generation).toHaveProperty("length");
    expect(mon.workers.length).toBeGreaterThan(0);
    expect(mon.analytics).toHaveProperty("estimatedClearSec");
  });

  it("runtime snapshot includes production queue depths", () => {
    runtimeEngine.start();
    productionRuntime.tick();
    // Force refresh snapshot
    const unsub = runtimeEngine.subscribe(() => undefined);
    const snap = runtimeEngine.getSnapshot();
    unsub();
    expect(snap.version).toBe("28.2");
    expect(snap.metrics).toHaveProperty("queueRender");
    expect(snap.productionWorkers?.length).toBeGreaterThan(0);
  });
});
