import { afterEach, describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import { ProgressiveAssetLoader } from "../assetLoader";
import { writeViewMode, readViewMode } from "../qualityProfile";
import {
  PARSE_CONCURRENCY,
  applyParseStarvation,
  canParseLightDuringInteraction,
  canStartFetch,
  canStartParse,
  classifyParseBand,
  fetchRetryDelayMs,
  isBackpressured,
  isPriorityCancelSafe,
  isRetryableFetchError,
  shouldDeferExtreme,
  WAITING_PARSE_COUNT_LIMIT,
} from "./parsePolicy";
import { ParseScheduler } from "./parseScheduler";
import { ParseDiagnostics } from "./parseDiagnostics";
import { inspectGlbHeader, GLB_MAGIC, GLTF_WORKER_FEASIBILITY } from "./glbInspect";
import { hasSchedulerPostTask, yieldForRenderOpportunity, yieldToScheduler } from "./browserYield";
import { supportsLongTaskObserver } from "./longTaskObserver";
import type { ParseJob } from "./parseScheduler";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function fakeGlb(bytes = 32): ArrayBuffer {
  const buf = new ArrayBuffer(bytes);
  const u8 = new Uint8Array(buf);
  u8.set([0x67, 0x6c, 0x54, 0x46]);
  const view = new DataView(buf);
  view.setUint32(4, 2, true);
  view.setUint32(8, bytes, true);
  return buf;
}

function meshRoot(id: string): THREE.Object3D {
  const g = new THREE.Group();
  g.name = id;
  g.add(new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshBasicMaterial({ color: 0x8899aa })));
  return g;
}

function job(over: Partial<ParseJob> & Pick<ParseJob, "id">): ParseJob {
  return {
    url: `/assets/odessa/${over.id}.glb`,
    buffer: fakeGlb(),
    sizeMb: 1,
    heavyClass: "LIGHT",
    score: 100,
    queuedAt: 0,
    parseBand: "MID",
    ...over,
  };
}

async function flush(ms = 0) {
  await Promise.resolve();
  await Promise.resolve();
  if (ms) await new Promise((r) => setTimeout(r, ms));
  await Promise.resolve();
}

function stubFetch(handler: (url: string, init?: RequestInit) => Promise<Response> | Response) {
  vi.stubGlobal("fetch", (url: string | URL, init?: RequestInit) => handler(String(url), init));
}

function okGlbResponse(): Response {
  return {
    ok: true,
    status: 200,
    headers: { get: () => null },
    arrayBuffer: async () => fakeGlb(),
  } as unknown as Response;
}

describe("parse policy", () => {
  it("classifies parse bands NEAR → MID → TARGET → FAR → EDGE → OUTSIDE", () => {
    const t = { nearM: 100, midM: 400, farM: 1000 };
    expect(classifyParseBand({ distanceM: 40, inFrustum: true, nearTarget: false, ...t })).toBe("NEAR");
    expect(classifyParseBand({ distanceM: 200, inFrustum: true, nearTarget: false, ...t })).toBe("MID");
    expect(classifyParseBand({ distanceM: 800, inFrustum: true, nearTarget: true, ...t })).toBe("TARGET");
    expect(classifyParseBand({ distanceM: 800, inFrustum: true, nearTarget: false, ...t })).toBe("FAR");
    expect(classifyParseBand({ distanceM: 800, inFrustum: false, nearTarget: false, ...t })).toBe("EDGE");
    expect(classifyParseBand({ distanceM: 4000, inFrustum: false, nearTarget: false, ...t })).toBe("OUTSIDE");
  });

  it("promotes starved bands without jumping to NEAR immediately", () => {
    expect(applyParseStarvation("OUTSIDE", 1000)).toBe("OUTSIDE");
    expect(applyParseStarvation("OUTSIDE", 8000)).toBe("EDGE");
    expect(applyParseStarvation("OUTSIDE", 16000)).toBe("FAR");
  });

  it("blocks MEDIUM/HEAVY/EXTREME parse start while INTERACTING; LIGHT only if measured safe", () => {
    const base = {
      mode: "INTERACTING" as const,
      fps: 60,
      lastParseMs: 10,
      bootState: "FILLING" as const,
      nearTarget: false,
      seaProtected: false,
      parseBand: "NEAR" as const,
      higherPriorityWaiting: false,
      currentlyParsing: false,
    };
    expect(canStartParse({ ...base, heavyClass: "LIGHT" })).toBe(true);
    expect(canStartParse({ ...base, heavyClass: "MEDIUM" })).toBe(false);
    expect(canStartParse({ ...base, heavyClass: "HEAVY" })).toBe(false);
    expect(canStartParse({ ...base, heavyClass: "EXTREME" })).toBe(false);
    expect(canParseLightDuringInteraction("LIGHT", 80, 60)).toBe(false);
    expect(canParseLightDuringInteraction("LIGHT", 10, 20)).toBe(false);
  });

  it("serializes heavy parse: a second cannot start while one is currently parsing", () => {
    expect(
      canStartParse({
        heavyClass: "HEAVY",
        mode: "IDLE",
        fps: 60,
        lastParseMs: 12,
        bootState: "FILLING",
        nearTarget: false,
        seaProtected: false,
        parseBand: "FAR",
        higherPriorityWaiting: false,
        currentlyParsing: true,
      }),
    ).toBe(false);
    expect(PARSE_CONCURRENCY).toBe(1);
  });

  it("defers EXTREME until settled unless sea/target protected", () => {
    expect(
      shouldDeferExtreme({
        heavyClass: "EXTREME",
        bootState: "INTERACTIVE",
        mode: "IDLE",
        nearTarget: false,
        seaProtected: false,
        higherPriorityWaiting: false,
      }),
    ).toBe(true);
    expect(
      shouldDeferExtreme({
        heavyClass: "EXTREME",
        bootState: "FILLING",
        mode: "IDLE",
        nearTarget: true,
        seaProtected: false,
        higherPriorityWaiting: false,
      }),
    ).toBe(false);
  });

  it("applies fetch backpressure except for sea/NEAR", () => {
    expect(
      isBackpressured({
        waitingParseCount: WAITING_PARSE_COUNT_LIMIT,
        waitingParseMb: 0,
        waitingActivationCount: 0,
        waitingActivationMb: 0,
      }),
    ).toBe(true);
    expect(canStartFetch({ backpressure: true, parseBand: "OUTSIDE" })).toBe(false);
    expect(canStartFetch({ backpressure: true, parseBand: "NEAR" })).toBe(true);
    expect(canStartFetch({ backpressure: true, seaProtected: true })).toBe(true);
    expect(canStartFetch({ backpressure: true, prefetch: true, parseBand: "FAR" })).toBe(false);
  });

  it("retries only network fetch errors with backoff, never GLTF parse failures", () => {
    expect(isRetryableFetchError("TypeError: Failed to fetch")).toBe(true);
    expect(isRetryableFetchError("HTTP 503")).toBe(true);
    expect(isRetryableFetchError("HTTP 404 /x.glb")).toBe(false);
    expect(isRetryableFetchError("INVALID_GLB_MAGIC:HTML")).toBe(false);
    expect(isRetryableFetchError("GLTF_NO_MESHES")).toBe(false);
    expect(isRetryableFetchError("priority_cancel")).toBe(false);
    expect(fetchRetryDelayMs(0)).toBe(400);
    expect(fetchRetryDelayMs(1)).toBe(1200);
  });

  it("will not AbortController-cancel sea, target, visible, or already-parsing assets", () => {
    expect(
      isPriorityCancelSafe({
        parsing: true,
        seaProtected: false,
        nearTarget: false,
        parseBand: "OUTSIDE",
        inFrustum: false,
      }),
    ).toBe(false);
    expect(
      isPriorityCancelSafe({
        parsing: false,
        seaProtected: true,
        nearTarget: false,
        parseBand: "OUTSIDE",
        inFrustum: false,
      }),
    ).toBe(false);
    expect(
      isPriorityCancelSafe({
        parsing: false,
        seaProtected: false,
        nearTarget: false,
        parseBand: "NEAR",
        inFrustum: true,
      }),
    ).toBe(false);
    expect(
      isPriorityCancelSafe({
        parsing: false,
        seaProtected: false,
        nearTarget: false,
        parseBand: "OUTSIDE",
        inFrustum: false,
      }),
    ).toBe(true);
  });
});

describe("ParseScheduler", () => {
  it("parses by visual band, not FIFO, and will not parse OUTSIDE ahead of visible NEAR", async () => {
    const parsed: string[] = [];
    const diag = new ParseDiagnostics();
    const scheduler = new ParseScheduler({
      parseFn: (j) => ({ root: meshRoot(j.id) }),
      diagnostics: diag,
      yieldFn: async () => undefined,
      now: () => 1000,
    });
    scheduler.setRuntime({ mode: "IDLE", fps: 60, bootState: "FILLING" });
    scheduler.setHandlers({
      onParsed: (id) => parsed.push(id),
      onFailed: () => undefined,
    });
    scheduler.enqueue(job({ id: "OUT", parseBand: "OUTSIDE", score: -50, sizeMb: 25, heavyClass: "HEAVY", queuedAt: 0 }));
    scheduler.enqueue(job({ id: "NEAR", parseBand: "NEAR", score: 80, queuedAt: 500 }));
    await scheduler.pump();
    expect(parsed[0]).toBe("NEAR");
    expect(parsed).toContain("OUT");
    scheduler.dispose();
  });

  it("does not start HEAVY/EXTREME while INTERACTING; resumes LIGHT-safe work", async () => {
    const parsed: string[] = [];
    const diag = new ParseDiagnostics();
    const scheduler = new ParseScheduler({
      parseFn: (j) => ({ root: meshRoot(j.id) }),
      diagnostics: diag,
      yieldFn: async () => undefined,
      now: () => 0,
    });
    scheduler.setHandlers({
      onParsed: (id) => parsed.push(id),
      onFailed: () => undefined,
    });
    scheduler.setRuntime({ mode: "INTERACTING", fps: 60, bootState: "FILLING" });
    scheduler.enqueue(job({ id: "H", heavyClass: "HEAVY", parseBand: "NEAR" }));
    scheduler.enqueue(job({ id: "L", heavyClass: "LIGHT", parseBand: "MID" }));
    await scheduler.pump();
    expect(parsed).toEqual(["L"]);
    scheduler.setRuntime({ mode: "IDLE", fps: 60, bootState: "FILLING" });
    await scheduler.pump();
    expect(parsed).toEqual(["L", "H"]);
    scheduler.dispose();
  });

  it("yields after each heavy parse before starting the next (no same-turn chain)", async () => {
    const parsed: string[] = [];
    const yields: boolean[] = [];
    let resume: (() => void) | null = null;
    const diag = new ParseDiagnostics();
    const scheduler = new ParseScheduler({
      parseFn: (j) => ({ root: meshRoot(j.id) }),
      diagnostics: diag,
      yieldFn: (heavy) => {
        yields.push(heavy);
        if (!heavy) return Promise.resolve();
        return new Promise((r) => {
          resume = r;
        });
      },
      now: () => 0,
    });
    scheduler.setRuntime({ mode: "IDLE", fps: 60, bootState: "FILLING" });
    scheduler.setHandlers({
      onParsed: (id) => parsed.push(id),
      onFailed: () => undefined,
    });
    scheduler.enqueue(job({ id: "H1", heavyClass: "HEAVY", parseBand: "NEAR", score: 1 }));
    scheduler.enqueue(job({ id: "H2", heavyClass: "HEAVY", parseBand: "MID", score: 2 }));
    const pumping = scheduler.pump();
    await flush();
    expect(parsed).toEqual(["H1"]);
    expect(yields).toEqual([true]);
    expect(scheduler.waitingCount()).toBe(1);
    resume?.();
    await flush();
    expect(parsed).toEqual(["H1", "H2"]);
    resume?.();
    await pumping;
    expect(yields).toEqual([true, true]);
    scheduler.dispose();
  });

  it("isolates a parse failure and continues the remaining queue", async () => {
    const parsed: string[] = [];
    const failed: string[] = [];
    const diag = new ParseDiagnostics();
    const scheduler = new ParseScheduler({
      parseFn: (j) => {
        if (j.id === "BAD") throw new Error("GLTF_NO_MESHES");
        return { root: meshRoot(j.id) };
      },
      diagnostics: diag,
      yieldFn: async () => undefined,
      now: () => 0,
    });
    scheduler.setRuntime({ mode: "IDLE", fps: 60, bootState: "FILLING" });
    scheduler.setHandlers({
      onParsed: (id) => parsed.push(id),
      onFailed: (id) => failed.push(id),
    });
    scheduler.enqueue(job({ id: "BAD", parseBand: "NEAR", score: 1 }));
    scheduler.enqueue(job({ id: "GOOD", parseBand: "MID", score: 2 }));
    await scheduler.pump();
    expect(failed).toEqual(["BAD"]);
    expect(parsed).toEqual(["GOOD"]);
    scheduler.dispose();
  });

  it("applies starvation promotion so a long-waiting EDGE can outrank a newer OUTSIDE", async () => {
    const parsed: string[] = [];
    let now = 20_000;
    const diag = new ParseDiagnostics();
    const scheduler = new ParseScheduler({
      parseFn: (j) => ({ root: meshRoot(j.id) }),
      diagnostics: diag,
      yieldFn: async () => undefined,
      now: () => now,
    });
    scheduler.setRuntime({ mode: "IDLE", fps: 60, bootState: "READY" });
    scheduler.setHandlers({
      onParsed: (id) => parsed.push(id),
      onFailed: () => undefined,
    });
    scheduler.enqueue(job({ id: "OLD", parseBand: "EDGE", score: 500, queuedAt: 0, sizeMb: 2 }));
    scheduler.enqueue(job({ id: "NEW", parseBand: "OUTSIDE", score: 10, queuedAt: 19_900, sizeMb: 25, heavyClass: "HEAVY" }));
    await scheduler.pump();
    expect(parsed[0]).toBe("OLD");
    scheduler.dispose();
  });
});

describe("ProgressiveAssetLoader pipeline", () => {
  it("keeps fetch concurrency independent of parse concurrency", async () => {
    const started: string[] = [];
    stubFetch((url, init) => {
      started.push(url);
      return new Promise((resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
      });
    });
    const loader = new ProgressiveAssetLoader({
      parseFn: (j) => ({ root: meshRoot(j.id) }),
      yieldFn: async () => undefined,
    });
    loader.setMaxConcurrent(2);
    loader.registerManifestAsset("t", { id: "A", url: "/a.glb", layer: "city", sizeMb: 1 });
    loader.registerManifestAsset("t", { id: "B", url: "/b.glb", layer: "city", sizeMb: 1 });
    loader.registerManifestAsset("t", { id: "C", url: "/c.glb", layer: "city", sizeMb: 1 });
    loader.registerManifestAsset("t", { id: "D", url: "/d.glb", layer: "city", sizeMb: 1 });
    loader.enqueue("A");
    loader.enqueue("B");
    loader.enqueue("C");
    loader.enqueue("D");
    await flush();
    expect(loader.fetchingCount()).toBe(2);
    expect(loader.fetchQueueLength()).toBe(2);
    expect(PARSE_CONCURRENCY).toBe(1);
    loader.cancelAll();
  });

  it("does not duplicate GLB requests for the same id", async () => {
    let fetches = 0;
    stubFetch(async () => {
      fetches += 1;
      return okGlbResponse();
    });
    const loader = new ProgressiveAssetLoader({
      parseFn: (j) => ({ root: meshRoot(j.id) }),
      yieldFn: async () => undefined,
    });
    loader.registerManifestAsset("t", { id: "A", url: "/a.glb", layer: "city", sizeMb: 1 });
    loader.enqueue("A");
    loader.enqueue("A");
    loader.enqueue("A", true);
    await flush(20);
    expect(fetches).toBe(1);
    loader.cancelAll();
  });

  it("retries a network fetch with backoff then succeeds", async () => {
    vi.useFakeTimers();
    let fetches = 0;
    stubFetch(async () => {
      fetches += 1;
      if (fetches < 3) throw new TypeError("Failed to fetch");
      return okGlbResponse();
    });
    const loader = new ProgressiveAssetLoader({
      parseFn: (j) => ({ root: meshRoot(j.id) }),
      yieldFn: async () => undefined,
    });
    loader.registerManifestAsset("t", { id: "A", url: "/a.glb", layer: "city", sizeMb: 1 });
    loader.enqueue("A");
    await vi.advanceTimersByTimeAsync(400);
    await vi.advanceTimersByTimeAsync(1200);
    await flush();
    expect(fetches).toBe(3);
    expect(loader.registry.get("A")?.status).toBe("loaded");
    loader.cancelAll();
    vi.useRealTimers();
  });

  it("does not retry a deterministic parse failure", async () => {
    let parses = 0;
    stubFetch(async () => okGlbResponse());
    const loader = new ProgressiveAssetLoader({
      parseFn: () => {
        parses += 1;
        throw new Error("GLTF_NO_MESHES");
      },
      yieldFn: async () => undefined,
    });
    loader.registerManifestAsset("t", { id: "A", url: "/a.glb", layer: "city", sizeMb: 1 });
    loader.enqueue("A");
    await flush(20);
    expect(parses).toBe(1);
    expect(loader.registry.get("A")?.status).toBe("failed");
    loader.enqueue("A");
    await flush();
    expect(parses).toBe(1);
    loader.cancelAll();
  });

  it("aborts a low-priority in-flight fetch via AbortController and returns the asset to idle", async () => {
    stubFetch((_url, init) => {
      return new Promise((_, reject) => {
        init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
      });
    });
    const cancelled: string[] = [];
    const loader = new ProgressiveAssetLoader({
      parseFn: (j) => ({ root: meshRoot(j.id) }),
      yieldFn: async () => undefined,
    });
    loader.onFetchCancelled = (id) => cancelled.push(id);
    loader.registerManifestAsset("t", { id: "FAR", url: "/far.glb", layer: "city", sizeMb: 8 });
    loader.updatePriority("FAR", {
      score: 9000,
      parseBand: "OUTSIDE",
      nearTarget: false,
      inFrustum: false,
      seaProtected: false,
    });
    loader.enqueue("FAR");
    await flush();
    expect(loader.fetchingCount()).toBe(1);
    loader.tickQueues();
    await flush();
    expect(cancelled).toContain("FAR");
    expect(loader.registry.get("FAR")?.status).toBe("idle");
    loader.cancelAll();
  });

  it("stops lower-priority fetches when the parse queue is backpressured", async () => {
    stubFetch(async () => okGlbResponse());
    const loader = new ProgressiveAssetLoader({
      parseFn: (j) => ({ root: meshRoot(j.id) }),
      yieldFn: async () => undefined,
    });
    loader.setRuntime({ mode: "INTERACTING", fps: 60, bootState: "FILLING", waitingActivationCount: 0, waitingActivationMb: 0 });
    for (const id of ["H1", "H2", "H3", "H4"]) {
      loader.registerManifestAsset("t", {
        id,
        url: `/${id}.glb`,
        layer: "heavy",
        sizeMb: 40,
        triangles: 900_000,
      });
      loader.updatePriority(id, {
        score: 4000,
        parseBand: "OUTSIDE",
        nearTarget: false,
        inFrustum: false,
        seaProtected: false,
      });
      loader.enqueue(id);
    }
    await flush(40);
    expect(loader.parseQueueLength()).toBeLessThanOrEqual(WAITING_PARSE_COUNT_LIMIT);
    expect(loader.pipelineSnapshot().backpressure || loader.parseQueueLength() >= WAITING_PARSE_COUNT_LIMIT).toBe(true);
    loader.cancelAll();
  });

  it("walks queued → fetching → waiting_parse → parsed and cleans up on remount", async () => {
    stubFetch(async () => okGlbResponse());
    const phases: string[] = [];
    const loader = new ProgressiveAssetLoader({
      parseFn: (j) => ({ root: meshRoot(j.id) }),
      yieldFn: async () => undefined,
    });
    loader.registerManifestAsset("t", { id: "A", url: "/a.glb", layer: "city", sizeMb: 0.4 });
    loader.subscribe((p) => {
      const row = loader.registry.get("A");
      if (row?.lifecycle) phases.push(row.lifecycle);
    });
    writeViewMode("3d");
    loader.enqueue("A");
    await flush(30);
    expect(loader.registry.get("A")?.lifecycle).toBe("parsed");
    expect(loader.registry.get("A")?.status).toBe("loaded");
    expect(phases).toContain("queued");
    expect(phases).toContain("fetching");
    loader.cancelAll();
    writeViewMode("2d");
    expect(readViewMode()).toBe("2d");
    expect(loader.parseQueueLength()).toBe(0);
    writeViewMode("3d");
  });
});

describe("Safari fallback scheduling + worker feasibility", () => {
  it("does not require postTask, SharedArrayBuffer, COI, or WebGPU", () => {
    expect(hasSchedulerPostTask()).toBe(false);
    expect(GLTF_WORKER_FEASIBILITY.fullGltfParseInWorker).toBe(false);
    expect(GLTF_WORKER_FEASIBILITY.requiresSharedArrayBuffer).toBe(false);
    expect(GLTF_WORKER_FEASIBILITY.requiresCrossOriginIsolation).toBe(false);
    expect(GLTF_WORKER_FEASIBILITY.requiresWebGPU).toBe(false);
    expect(supportsLongTaskObserver()).toBeTypeOf("boolean");
  });

  it("yields via setTimeout when requestAnimationFrame is missing", async () => {
    vi.stubGlobal("requestAnimationFrame", undefined);
    vi.useFakeTimers();
    const p = yieldForRenderOpportunity();
    await vi.runAllTimersAsync();
    await p;
    const p2 = yieldToScheduler();
    await vi.runAllTimersAsync();
    await p2;
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("inspects GLB headers without copying the buffer", () => {
    const buf = fakeGlb(48);
    const info = inspectGlbHeader(buf);
    expect(info.magic).toBe(GLB_MAGIC);
    expect(info.version).toBe(2);
    expect(info.length).toBe(48);
    expect(() => inspectGlbHeader(new ArrayBuffer(4))).toThrow(/INVALID_GLB_MAGIC/);
  });
});
