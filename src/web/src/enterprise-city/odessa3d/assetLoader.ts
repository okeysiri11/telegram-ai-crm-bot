/**
 * Progressive GLB loader — fetch, parse, and activation are separate queues.
 * GLTFLoader.parse stays on the main thread; a scheduler yields between parses.
 */

import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { AssetRegistry } from "./assetRegistry";
import { resolvePublicAssetUrl } from "./publicAssetUrl";
import type {
  AssetLoadDiagnostic,
  AssetLoadPhase,
  CityAsset,
  CityBounds,
  LoadingProgress,
  OdessaManifestAsset,
} from "./types";
import { manifestProgress } from "./odessaManifest";
import { disposeObject3D } from "./disposeUtils";
import { classifyHeavyAsset } from "./assetLifecycle";
import type { BootState } from "./assetLifecycle";
import type { RuntimePerfMode } from "./runtimePerfState";
import { ParseDiagnostics } from "./loading/parseDiagnostics";
import type { GlbPipelineDiagnostics, PipelineQueueSnapshot } from "./loading/parseDiagnostics";
import { ParseScheduler } from "./loading/parseScheduler";
import type { ParseFn, ParseJob } from "./loading/parseScheduler";
import {
  FETCH_RETRY_MAX,
  PARSE_CONCURRENCY,
  canStartFetch,
  classifyParseBand,
  fetchRetryDelayMs,
  isBackpressured,
  isPriorityCancelSafe,
  isRetryableFetchError,
  type ParseBand,
} from "./loading/parsePolicy";
import { inspectGlbHeader, GLB_MAGIC } from "./loading/glbInspect";
import { yieldAfterParse } from "./loading/browserYield";

const DEBUG_PLACEHOLDER = import.meta.env.DEV && import.meta.env.VITE_ODESSA_DEBUG_PLACEHOLDER === "true";

export type AssetEnqueueOpts = {
  prefetch?: boolean;
};

export type AssetPriorityPatch = {
  score: number;
  parseBand: ParseBand;
  nearTarget: boolean;
  inFrustum: boolean;
  seaProtected: boolean;
  screenImportant?: boolean;
  distanceM?: number;
};

export type LoaderRuntimeState = {
  mode: RuntimePerfMode;
  fps: number;
  bootState: BootState;
  waitingActivationCount: number;
  waitingActivationMb: number;
};

export type ProgressiveAssetLoaderOptions = {
  parseFn?: ParseFn;
  yieldFn?: (heavy: boolean) => Promise<void>;
  now?: () => number;
};

function layerColor(layerId: string): number {
  switch (layerId) {
    case "city":
      return 0x5a6a7a;
    case "heavy":
      return 0x6a5a4a;
    default:
      return 0x666677;
  }
}

function proceduralMesh(asset: CityAsset): THREE.Object3D {
  const b = asset.bounds;
  const w = b ? Math.max(20, b.maxX - b.minX) : 120;
  const d = b ? Math.max(20, b.maxZ - b.minZ) : 120;
  const h = b ? Math.max(4, (b.maxY ?? 2) - (b.minY ?? 0)) : 8;
  const geo = new THREE.BoxGeometry(w, h, d);
  const mat = new THREE.MeshStandardMaterial({
    color: layerColor(asset.layerId || "city"),
    transparent: true,
    opacity: 0.35,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.y = h / 2;
  const group = new THREE.Group();
  group.name = asset.id;
  group.add(mesh);
  return group;
}

function timeoutMsForAsset(sizeMb = 8): number {
  return Math.min(180_000, Math.max(90_000, sizeMb * 12_000));
}

function countMeshes(root: THREE.Object3D): number {
  let n = 0;
  root.traverse((c) => {
    if ((c as THREE.Mesh).isMesh) n += 1;
  });
  return n;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const defaultParseFn: ParseFn = async (job) => {
  const gltf = await new Promise<import("three/examples/jsm/loaders/GLTFLoader.js").GLTF>((resolve, reject) => {
    const gltfLoader = new GLTFLoader();
    gltfLoader.parse(
      job.buffer,
      job.url,
      (g) => resolve(g),
      (err) => reject(err instanceof Error ? err : new Error(String(err))),
    );
  });
  return { root: gltf.scene, objectCount: countMeshes(gltf.scene) };
};

type FetchSlot = {
  id: string;
  abort: AbortController;
  prefetch: boolean;
};

export class ProgressiveAssetLoader {
  readonly registry = new AssetRegistry();
  private fetchQueue: string[] = [];
  private fetchActive = new Map<string, FetchSlot>();
  private maxFetchConcurrent = 2;
  private listeners = new Set<(p: LoadingProgress) => void>();
  private loadingAssetId: string | null = null;
  private totalMb = 0;
  private diagnostics = new Map<string, AssetLoadDiagnostic>();
  private pipelineDiag = new ParseDiagnostics();
  private aborted = false;
  private streamingPaused = false;
  private prefetchFlags = new Set<string>();
  private priorities = new Map<string, AssetPriorityPatch>();
  private retryCount = new Map<string, number>();
  private failedParse = new Set<string>();
  private priorityCancels = new Set<string>();
  private runtime: LoaderRuntimeState = {
    mode: "IDLE",
    fps: 60,
    bootState: "BOOTSTRAP",
    waitingActivationCount: 0,
    waitingActivationMb: 0,
  };
  private scheduler: ParseScheduler;
  private now: () => number;
  onFetchCancelled: ((assetId: string) => void) | null = null;

  constructor(opts: ProgressiveAssetLoaderOptions = {}) {
    this.now = opts.now ?? (() => performance.now());
    this.scheduler = new ParseScheduler({
      parseFn: opts.parseFn ?? defaultParseFn,
      diagnostics: this.pipelineDiag,
      yieldFn: opts.yieldFn ?? yieldAfterParse,
      now: this.now,
    });
    this.scheduler.setHandlers({
      onParsed: (id, result, parseMs) => this.handleParsed(id, result, parseMs),
      onFailed: (id, error) => this.handleParseFailed(id, error),
    });
  }

  setMaxConcurrent(n: number) {
    this.maxFetchConcurrent = Math.max(1, n);
    this.pumpFetch();
  }

  getMaxFetchConcurrent(): number {
    return this.maxFetchConcurrent;
  }

  setStreamingPaused(paused: boolean) {
    this.streamingPaused = paused;
    if (!paused) this.pumpFetch();
    void this.scheduler.pump();
  }

  isStreamingPaused() {
    return this.streamingPaused;
  }

  setRuntime(runtime: Partial<LoaderRuntimeState>) {
    this.runtime = { ...this.runtime, ...runtime };
    this.scheduler.setRuntime({
      mode: this.runtime.mode,
      fps: this.runtime.fps,
      bootState: this.runtime.bootState,
    });
  }

  updatePriority(id: string, patch: AssetPriorityPatch) {
    this.priorities.set(id, patch);
    this.scheduler.updatePriority(id, {
      score: patch.score,
      parseBand: patch.parseBand,
      nearTarget: patch.nearTarget,
      inFrustum: patch.inFrustum,
      seaProtected: patch.seaProtected,
      screenImportant: patch.screenImportant,
    });
  }

  allowsPrefetch(): boolean {
    if (this.runtime.mode !== "IDLE") return false;
    if (this.runtime.bootState === "BOOTSTRAP") return false;
    return !this.backpressure() && this.scheduler.waitingCount() === 0;
  }

  tickQueues() {
    this.cancelStaleFetches();
    this.pumpFetch();
    void this.scheduler.pump();
  }

  registerManifestAsset(tileId: string, asset: OdessaManifestAsset): CityAsset {
    if (asset.sizeMb) this.totalMb += asset.sizeMb;
    const url = resolvePublicAssetUrl(asset.url);
    return this.registry.register({
      id: asset.id,
      url,
      tileId,
      layerId: asset.layer,
      lod: asset.lod,
      priority: asset.priority ?? 5,
      bounds: asset.bounds,
      sizeMb: asset.sizeMb,
      triangleCount: asset.triangles,
      objectCount: asset.objects,
      heavyClass: classifyHeavyAsset({
        triangles: asset.triangles,
        sizeMb: asset.sizeMb,
        layerId: asset.layer,
      }),
      entityRefs: asset.entityRef ? [asset.entityRef] : undefined,
      loadPhase: "idle",
      lifecycle: undefined,
    });
  }

  enqueue(assetId: string, front = false, opts?: AssetEnqueueOpts) {
    if (this.aborted) return;
    const row = this.registry.get(assetId);
    if (!row) return;
    if (row.status === "loaded" || row.status === "loading" || row.status === "queued" || row.status === "failed") return;
    if (row.lifecycle === "waiting_parse" || row.lifecycle === "parsing") return;
    if (this.failedParse.has(assetId)) return;
    if (this.fetchQueue.includes(assetId) || this.fetchActive.has(assetId) || this.scheduler.hasId(assetId)) return;
    this.registry.update(assetId, { status: "queued", loadPhase: "queued", lifecycle: "queued" });
    this.patchDiag(assetId, { phase: "queued", url: row.url });
    if (opts?.prefetch) this.prefetchFlags.add(assetId);
    else this.prefetchFlags.delete(assetId);
    if (front) this.fetchQueue.unshift(assetId);
    else this.fetchQueue.push(assetId);
    this.sortFetchQueue();
    this.emit();
    this.pumpFetch();
  }

  subscribe(fn: (p: LoadingProgress) => void) {
    this.listeners.add(fn);
    fn(this.progress());
    return () => this.listeners.delete(fn);
  }

  getLoadDiagnostics(): AssetLoadDiagnostic[] {
    return [...this.diagnostics.values()];
  }

  pipelineSnapshot(activationPending = 0, activationMb = 0): GlbPipelineDiagnostics {
    return this.pipelineDiag.snapshot(this.queueSnapshot(activationPending, activationMb));
  }

  fetchQueueLength(): number {
    return this.fetchQueue.length;
  }

  parseQueueLength(): number {
    return this.scheduler.waitingCount();
  }

  fetchingCount(): number {
    return this.fetchActive.size;
  }

  isParseBusy(): boolean {
    return this.scheduler.isParsing() || this.scheduler.waitingCount() > 0;
  }

  currentParseId(): string | null {
    return this.scheduler.currentParseId();
  }

  recordPrep(id: string, prepMs: number) {
    this.pipelineDiag.recordPrep(id, prepMs);
  }

  recordAttach(id: string, attachMs: number) {
    this.pipelineDiag.recordAttach(id, attachMs);
  }

  progress(): LoadingProgress {
    const rows = this.registry.list();
    const c = this.registry.counts();
    const loadedMb = rows
      .filter((a) => a.source === "REAL_GLB" && (a.status === "loaded" || a.loadPhase === "downloaded" || a.loadPhase === "parsing" || a.loadPhase === "parsed"))
      .reduce((s, a) => s + (a.sizeMb ?? 0), 0);
    const parsedCount = rows.filter((a) => {
      const life = a.lifecycle;
      return a.source === "REAL_GLB" && (life === "parsed" || life === "preparing" || life === "ready" || life === "active" || life === "hidden");
    }).length;
    const downloadedCount = rows.filter((a) => (a.timings?.fetchMs ?? 0) > 0 || a.loadPhase === "downloaded" || a.loadPhase === "parsing" || a.status === "loaded").length;
    const realGlbLoaded = c.realGlb;
    const diags = this.getLoadDiagnostics();
    const firstError = diags.find((d) => d.phase === "failed" && d.error)?.error ?? null;
    const pipe = this.pipelineSnapshot(this.runtime.waitingActivationCount, this.runtime.waitingActivationMb);

    return manifestProgress(c.total, c.loaded, c.failed, c.queued, c.loading, {
      loadingAssetId: this.loadingAssetId ?? this.scheduler.currentParseId(),
      loadedMb: +loadedMb.toFixed(2),
      totalMb: +this.totalMb.toFixed(2),
      realGlbLoaded,
      sourceMode: realGlbLoaded > 0 ? "REAL_GLB" : c.failed ? "MIXED" : "REAL_GLB",
      loadDiagnostics: diags.filter((d) => d.phase !== "idle"),
      firstError,
      parsedCount,
      downloadedCount,
      currentAssetId: this.loadingAssetId ?? this.scheduler.currentParseId(),
      waitingParse: pipe.waitingParse,
    });
  }

  cancelAll() {
    this.aborted = true;
    this.fetchQueue.length = 0;
    for (const slot of this.fetchActive.values()) slot.abort.abort();
    this.fetchActive.clear();
    this.scheduler.dispose();
    this.pipelineDiag.dispose();
    this.loadingAssetId = null;
    this.prefetchFlags.clear();
    this.priorities.clear();
    for (const row of this.registry.list()) {
      if (row.status === "loading" || row.status === "queued") {
        if (row.object3D && !row.object3D.parent) disposeObject3D(row.object3D);
        this.registry.update(row.id, {
          status: "failed",
          loadPhase: "failed",
          lifecycle: "failed",
          error: "aborted",
          object3D: null,
        });
        this.patchDiag(row.id, { phase: "failed", error: "aborted" });
      } else if (row.object3D && !row.object3D.parent && row.lifecycle !== "active" && row.lifecycle !== "hidden") {
        disposeObject3D(row.object3D);
        this.registry.update(row.id, { object3D: null, lifecycle: "failed", status: row.status === "loaded" ? "unloaded" : row.status });
      }
    }
    this.emit();
  }

  unloadAsset(id: string, opts?: { disposeSceneGraph?: boolean }) {
    const row = this.registry.get(id);
    if (!row) return;
    if (this.scheduler.hasId(id) && !this.scheduler.isParsing()) {
      this.scheduler.drop(id);
    }
    if (opts?.disposeSceneGraph !== false && row.object3D) {
      disposeObject3D(row.object3D);
    }
    this.registry.update(id, {
      status: "unloaded",
      object3D: null,
      loadPhase: "idle",
      lifecycle: undefined,
    });
    this.fetchQueue = this.fetchQueue.filter((q) => q !== id);
    this.emit();
  }

  private sortFetchQueue() {
    this.fetchQueue.sort((a, b) => this.fetchRank(a) - this.fetchRank(b));
  }

  private fetchRank(id: string): number {
    const p = this.priorities.get(id);
    const prefetch = this.prefetchFlags.has(id) ? 10_000 : 0;
    if (!p) return prefetch;
    const bandOrder = { NEAR: 0, MID: 1, TARGET: 2, FAR: 3, EDGE: 4, OUTSIDE: 5 };
    return bandOrder[p.parseBand] * 10_000 + p.score + prefetch;
  }

  private backpressure(): boolean {
    return isBackpressured({
      waitingParseCount: this.scheduler.waitingCount() + this.fetchActive.size,
      waitingParseMb: this.scheduler.waitingMb(),
      waitingActivationCount: this.runtime.waitingActivationCount,
      waitingActivationMb: this.runtime.waitingActivationMb,
    });
  }

  private pumpFetch() {
    if (this.aborted || this.streamingPaused) return;
    this.sortFetchQueue();
    while (this.fetchActive.size < this.maxFetchConcurrent && this.fetchQueue.length) {
      const id = this.fetchQueue.shift()!;
      const row = this.registry.get(id);
      if (!row || row.status !== "queued") continue;
      const pri = this.priorities.get(id);
      if (
        !canStartFetch({
          backpressure: this.backpressure(),
          prefetch: this.prefetchFlags.has(id),
          seaProtected: pri?.seaProtected,
          nearTarget: pri?.nearTarget,
          parseBand: pri?.parseBand,
        })
      ) {
        this.fetchQueue.unshift(id);
        break;
      }
      const abort = new AbortController();
      this.fetchActive.set(id, { id, abort, prefetch: this.prefetchFlags.has(id) });
      void this.fetchOne(row, abort)
        .catch(() => {})
        .finally(() => {
          this.fetchActive.delete(id);
          if (this.loadingAssetId === id && !this.scheduler.isParsing()) this.loadingAssetId = null;
          this.emit();
          this.pumpFetch();
          void this.scheduler.pump();
        });
    }
  }

  private cancelStaleFetches() {
    for (const [id, slot] of [...this.fetchActive.entries()]) {
      const pri = this.priorities.get(id);
      if (!pri) continue;
      if (
        isPriorityCancelSafe({
          parsing: false,
          seaProtected: pri.seaProtected,
          nearTarget: pri.nearTarget,
          parseBand: pri.parseBand,
          inFrustum: pri.inFrustum,
        })
      ) {
        this.priorityCancels.add(id);
        slot.abort.abort();
      }
    }
  }

  private async fetchOne(row: CityAsset, abort: AbortController): Promise<void> {
    if (this.aborted) return;
    this.loadingAssetId = row.id;
    this.registry.update(row.id, { status: "loading", error: undefined, loadPhase: "fetching", lifecycle: "fetching" });
    this.emit();

    const timer = window.setTimeout(() => abort.abort(), timeoutMsForAsset(row.sizeMb));
    try {
      const existing = this.registry.getByUrl(row.url);
      if (
        existing &&
        existing.id !== row.id &&
        existing.status === "loaded" &&
        existing.object3D &&
        existing.source === "REAL_GLB"
      ) {
        const clone = existing.object3D.clone(true);
        this.registry.update(row.id, {
          status: "loaded",
          object3D: clone,
          procedural: false,
          source: "REAL_GLB",
          loadPhase: "parsed",
          lifecycle: "parsed",
        });
        this.patchDiag(row.id, { phase: "parsed", url: row.url, meshCount: countMeshes(clone) });
        return;
      }

      const buffer = await this.fetchGlbBufferWithRetry(row.url, row, abort.signal);
      if (this.aborted || abort.signal.aborted) {
        this.revertCancelledFetch(row.id);
        return;
      }
      inspectGlbHeader(buffer);
      const latest = this.registry.get(row.id);
      const fetchMs = latest?.timings?.fetchMs ?? 0;
      this.registry.update(row.id, { loadPhase: "downloaded", lifecycle: "waiting_parse" });
      this.patchDiag(row.id, { phase: "downloaded", fetchMs });
      const pri = this.priorities.get(row.id);
      const job: ParseJob = {
        id: row.id,
        url: row.url,
        buffer,
        sizeMb: row.sizeMb ?? buffer.byteLength / 1_000_000,
        heavyClass: classifyHeavyAsset({
          triangles: row.triangleCount,
          sizeMb: row.sizeMb,
          layerId: row.layerId,
        }),
        score: pri?.score ?? 0,
        queuedAt: this.now(),
        prefetch: this.prefetchFlags.has(row.id),
        seaProtected: pri?.seaProtected,
        nearTarget: pri?.nearTarget,
        inFrustum: pri?.inFrustum,
        screenImportant: pri?.screenImportant,
        parseBand: pri?.parseBand ?? "MID",
        triangleCount: row.triangleCount,
        objectCount: row.objectCount,
      };
      this.scheduler.enqueue(job);
    } catch (err) {
      if (this.aborted) return;
      if (abort.signal.aborted) {
        if (this.priorityCancels.has(row.id)) {
          this.revertCancelledFetch(row.id);
          return;
        }
        const msg = err instanceof Error ? err.message : String(err);
        this.failAsset(row, msg || "fetch_timeout");
        return;
      }
      const msg = err instanceof Error ? err.message : String(err);
      this.failAsset(row, msg);
    } finally {
      window.clearTimeout(timer);
      this.emit();
    }
  }

  private async fetchGlbBufferWithRetry(url: string, asset: CityAsset, signal: AbortSignal): Promise<ArrayBuffer> {
    let lastError: Error | null = null;
    const max = FETCH_RETRY_MAX;
    for (let attempt = 0; attempt <= max; attempt += 1) {
      if (signal.aborted) throw new Error("aborted");
      try {
        return await this.fetchGlbBuffer(url, asset, signal);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        lastError = err instanceof Error ? err : new Error(msg);
        if (signal.aborted) throw lastError;
        if (!isRetryableFetchError(msg) || attempt >= max) throw lastError;
        this.retryCount.set(asset.id, attempt + 1);
        await sleep(fetchRetryDelayMs(attempt));
      }
    }
    throw lastError ?? new Error("fetch failed");
  }

  private async fetchGlbBuffer(url: string, asset: CityAsset, signal: AbortSignal): Promise<ArrayBuffer> {
    const started = this.now();
    this.registry.update(asset.id, { loadPhase: "fetching", lifecycle: "fetching" });
    this.patchDiag(asset.id, { phase: "fetching", url, elapsedMs: 0, sizeMb: asset.sizeMb });

    const res = await fetch(url, { cache: "force-cache", signal });
    const httpStatus = res.status;
    if (!res.ok) {
      throw new Error(`HTTP ${httpStatus} ${url}`);
    }
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("text/html")) {
      throw new Error(`HTML_RESPONSE_NOT_GLB ${url}`);
    }

    const total = Number(res.headers.get("content-length") || 0) || undefined;
    const bufStarted = this.now();
    const buf = await res.arrayBuffer();
    const arrayBufferMs = Math.round(this.now() - bufStarted);
    const fetchMs = Math.round(this.now() - started);
    const magic = new TextDecoder().decode(new Uint8Array(buf, 0, 4));
    if (magic !== GLB_MAGIC) {
      throw new Error(`INVALID_GLB_MAGIC:${magic} url=${url}`);
    }

    this.registry.update(asset.id, {
      loadPhase: "downloaded",
      timings: { ...(asset.timings || {}), fetchMs, arrayBufferMs },
    });
    this.patchDiag(asset.id, {
      phase: "downloaded",
      bytesLoaded: buf.byteLength,
      bytesTotal: total ?? buf.byteLength,
      httpStatus,
      elapsedMs: fetchMs,
      fetchMs,
      arrayBufferMs,
      sizeMb: asset.sizeMb,
    });
    this.pipelineDiag.recordFetch(asset.id, { url, sizeMb: asset.sizeMb ?? 0, fetchMs });
    return buf;
  }

  private revertCancelledFetch(id: string) {
    this.priorityCancels.delete(id);
    const row = this.registry.get(id);
    if (!row) return;
    this.registry.update(id, {
      status: "idle",
      loadPhase: "idle",
      lifecycle: undefined,
      error: undefined,
    });
    this.fetchQueue = this.fetchQueue.filter((q) => q !== id);
    this.patchDiag(id, { phase: "idle" });
    this.onFetchCancelled?.(id);
  }

  private failAsset(row: CityAsset, msg: string) {
    console.error("[Odessa3D] REAL_GLB failed:", row.id, row.url, msg);
    this.pipelineDiag.recordFailure(row.id, row.url, row.lifecycle || "fetching", msg, row.sizeMb);
    this.patchDiag(row.id, { phase: "failed", error: msg });
    if (DEBUG_PLACEHOLDER) {
      const root = proceduralMesh(row);
      this.registry.update(row.id, {
        status: "loaded",
        object3D: root,
        procedural: true,
        source: "PROCEDURAL_FALLBACK",
        error: msg,
        loadPhase: "parsed",
        lifecycle: "parsed",
      });
    } else {
      this.registry.update(row.id, {
        status: "failed",
        object3D: null,
        procedural: false,
        loadPhase: "failed",
        lifecycle: "failed",
        error: msg,
      });
    }
  }

  private handleParsed(id: string, result: { root: THREE.Object3D; objectCount?: number }, parseMs: number) {
    const row = this.registry.get(id);
    if (!row || this.aborted) {
      if (result.root && !result.root.parent) disposeObject3D(result.root);
      return;
    }
    const root = result.root;
    root.name = id;
    const meshes = result.objectCount ?? countMeshes(root);
    if (meshes === 0) {
      this.failedParse.add(id);
      this.handleParseFailed(id, new Error("GLTF_NO_MESHES"));
      return;
    }
    const fetchMs = row.timings?.fetchMs ?? 0;
    this.registry.update(id, {
      status: "loaded",
      object3D: root,
      procedural: false,
      source: "REAL_GLB",
      loadPhase: "parsed",
      lifecycle: "parsed",
      objectCount: meshes,
      timings: {
        ...row.timings,
        fetchMs,
        parseMs,
        objectCount: meshes,
        triangleCount: row.triangleCount,
        totalBlockingMs: parseMs,
      },
      heavyClass: classifyHeavyAsset({
        triangles: row.triangleCount,
        sizeMb: row.sizeMb,
        layerId: row.layerId,
      }),
    });
    this.patchDiag(id, {
      phase: "parsed",
      meshCount: meshes,
      fetchMs,
      parseMs,
      sizeMb: row.sizeMb,
      triangleCount: row.triangleCount,
      objectCount: meshes,
    });
    this.emit();
  }

  private handleParseFailed(id: string, error: Error) {
    this.failedParse.add(id);
    const row = this.registry.get(id);
    if (!row) return;
    this.failAsset(row, error.message);
    this.emit();
  }

  private queueSnapshot(activationPending: number, activationMb: number): PipelineQueueSnapshot {
    const rows = this.registry.list();
    const mb = (pred: (a: CityAsset) => boolean) =>
      +rows.filter(pred).reduce((s, a) => s + (a.sizeMb ?? 0), 0).toFixed(2);
    const count = (pred: (a: CityAsset) => boolean) => rows.filter(pred).length;
    const parsingId = this.scheduler.currentParseId();
    return {
      fetching: this.fetchActive.size,
      waitingParse: this.scheduler.waitingCount(),
      parsing: parsingId ? 1 : 0,
      parsed: count((a) => a.lifecycle === "parsed" || a.lifecycle === "preparing" || a.lifecycle === "ready"),
      waitingActivation: activationPending,
      active: count((a) => a.lifecycle === "active"),
      hidden: count((a) => a.lifecycle === "hidden"),
      failed: count((a) => a.lifecycle === "failed" || a.status === "failed"),
      fetchingMb: mb((a) => a.lifecycle === "fetching"),
      waitingParseMb: +this.scheduler.waitingMb().toFixed(2),
      parsingMb: parsingId ? this.registry.get(parsingId)?.sizeMb ?? 0 : 0,
      parsedMb: mb((a) => a.lifecycle === "parsed" || a.lifecycle === "preparing" || a.lifecycle === "ready"),
      waitingActivationMb: +activationMb.toFixed(2),
      activeMb: mb((a) => a.lifecycle === "active"),
      hiddenMb: mb((a) => a.lifecycle === "hidden"),
      fetchQueue: this.fetchQueue.length,
      parseQueue: this.scheduler.waitingCount(),
      activationQueue: activationPending,
      fetchConcurrent: this.maxFetchConcurrent,
      parseConcurrent: PARSE_CONCURRENCY,
      backpressure: this.backpressure(),
    };
  }

  private patchDiag(id: string, patch: Partial<AssetLoadDiagnostic>) {
    const cur = this.diagnostics.get(id) ?? { id, url: patch.url || "", phase: "idle" as AssetLoadPhase };
    this.diagnostics.set(id, { ...cur, ...patch, id });
  }

  private emit() {
    for (const fn of this.listeners) fn(this.progress());
  }
}

export function boundsFromManifest(b?: CityBounds): THREE.Box3 | null {
  if (!b) return null;
  return new THREE.Box3(
    new THREE.Vector3(b.minX, b.minY ?? 0, b.minZ),
    new THREE.Vector3(b.maxX, b.maxY ?? 50, b.maxZ),
  );
}

/** Node/browser smoke helper — same fetch + parse path as production loader. */
export async function smokeLoadGlb(url: string): Promise<{
  url: string;
  bytes: number;
  meshCount: number;
  box: { min: number[]; max: number[]; center: number[]; size: number[] };
}> {
  const resolved = resolvePublicAssetUrl(url);
  const res = await fetch(resolved);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const buf = await res.arrayBuffer();
  inspectGlbHeader(buf);
  const gltf = await new Promise<import("three/examples/jsm/loaders/GLTFLoader.js").GLTF>((resolve, reject) => {
    new GLTFLoader().parse(buf, resolved, resolve, (e) => reject(e instanceof Error ? e : new Error(String(e))));
  });
  const box = new THREE.Box3().setFromObject(gltf.scene);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  return {
    url: resolved,
    bytes: buf.byteLength,
    meshCount: countMeshes(gltf.scene),
    box: {
      min: box.min.toArray(),
      max: box.max.toArray(),
      center: center.toArray(),
      size: size.toArray(),
    },
  };
}

export { classifyParseBand };
