import { afterEach, describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import {
  activationBudgetMs,
  canActivateThisFrame,
  canTransitionLifecycle,
  classifyHeavyAsset,
  resolveBootState,
  scoreActivationPriority,
  transitionLifecycle,
} from "./assetLifecycle";
import { ProgressiveSceneActivator, type ActivatorTickContext } from "./progressiveActivator";
import { cacheManifestCenter, cacheMeasuredBounds, clearBoundsCache, getCachedCenter, getMeasuredBounds } from "./assetBoundsCache";
import { hasRequestIdleCallback, scheduleIdleWork } from "./idleCallback";
import { AssetRegistry } from "./assetRegistry";
import { writeViewMode, readViewMode } from "./qualityProfile";
import type { CityAsset } from "./types";

afterEach(() => {
  clearBoundsCache();
  vi.useRealTimers();
});

function stubAsset(id: string, patch: Partial<CityAsset> = {}): CityAsset {
  const root = patch.object3D ?? new THREE.Group();
  if (!patch.object3D) {
    root.name = id;
    root.add(new THREE.Mesh(new THREE.BoxGeometry(2, 2, 2), new THREE.MeshStandardMaterial({ color: 0x8899aa })));
  }
  return {
    id,
    url: `/assets/odessa/${id}.glb`,
    status: "loaded",
    source: "REAL_GLB",
    lifecycle: "parsed",
    object3D: root,
    tileId: id,
    layerId: "city",
    bounds: { minX: 0, maxX: 20, minZ: 0, maxZ: 20, minY: 0, maxY: 8 },
    triangleCount: 80,
    objectCount: 2,
    heavyClass: "LIGHT",
    sizeMb: 0.2,
    ...patch,
    object3D: patch.object3D ?? root,
  };
}

function tickCtx(over: Partial<ActivatorTickContext> = {}): ActivatorTickContext {
  const camera = over.camera ?? new THREE.PerspectiveCamera(50, 1, 0.1, 8000);
  if (!over.camera) {
    camera.position.set(0, 40, 80);
    camera.lookAt(0, 0, 0);
    camera.updateMatrixWorld();
  }
  const frustum = over.frustum ?? new THREE.Frustum();
  if (!over.frustum) {
    frustum.setFromProjectionMatrix(
      new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse),
    );
  }
  return {
    now: 0,
    mode: "IDLE",
    fps: 60,
    camera,
    target: new THREE.Vector3(0, 0, 0),
    frustum,
    priorityIds: new Set(),
    enableShadows: false,
    maxAnisotropy: 1,
    ...over,
  };
}

describe("Odessa asset lifecycle", () => {
  it("allows legal transitions and rejects illegal ones", () => {
    expect(canTransitionLifecycle("queued", "fetching")).toBe(true);
    expect(canTransitionLifecycle("fetching", "waiting_parse")).toBe(true);
    expect(canTransitionLifecycle("waiting_parse", "parsing")).toBe(true);
    expect(canTransitionLifecycle("parsed", "preparing")).toBe(true);
    expect(canTransitionLifecycle("ready", "active")).toBe(true);
    expect(canTransitionLifecycle("active", "hidden")).toBe(true);
    expect(canTransitionLifecycle("hidden", "active")).toBe(true);
    expect(canTransitionLifecycle("parsed", "active")).toBe(false);
    expect(() => transitionLifecycle("queued", "active")).toThrow(/invalid_lifecycle/);
    expect(transitionLifecycle("parsed", "parsed")).toBe("parsed");
  });

  it("classifies LIGHT / MEDIUM / HEAVY / EXTREME from triangles and size fallback", () => {
    expect(classifyHeavyAsset({ triangles: 10_000 })).toBe("LIGHT");
    expect(classifyHeavyAsset({ triangles: 250_000 })).toBe("MEDIUM");
    expect(classifyHeavyAsset({ triangles: 900_000 })).toBe("HEAVY");
    expect(classifyHeavyAsset({ triangles: 2_000_000 })).toBe("EXTREME");
    expect(classifyHeavyAsset({ sizeMb: 40 })).toBe("HEAVY");
    expect(classifyHeavyAsset({ triangles: 10, layerId: "heavy" })).toBe("MEDIUM");
  });

  it("resolves boot phases BOOTSTRAP → INTERACTIVE → FILLING → READY", () => {
    expect(resolveBootState({ total: 45, failed: 0, active: 0 })).toBe("BOOTSTRAP");
    expect(resolveBootState({ total: 45, failed: 0, active: 1 })).toBe("INTERACTIVE");
    expect(resolveBootState({ total: 45, failed: 0, active: 8 })).toBe("FILLING");
    expect(resolveBootState({ total: 45, failed: 0, active: 45 })).toBe("READY");
    expect(resolveBootState({ total: 45, failed: 2, active: 43 })).toBe("READY");
  });
});

describe("Odessa activation budget and priority", () => {
  it("uses zero budget while INTERACTING and a small SETTLING budget", () => {
    expect(activationBudgetMs("INTERACTING", 60)).toBe(0);
    expect(activationBudgetMs("SETTLING", 60)).toBe(2);
    expect(activationBudgetMs("IDLE", 60)).toBeGreaterThan(5);
    expect(activationBudgetMs("IDLE", 20)).toBe(3);
  });

  it("never activates two HEAVY/EXTREME assets in the same frame", () => {
    expect(canActivateThisFrame(0, 14, 6, "EXTREME")).toBe(true);
    expect(canActivateThisFrame(14, 14, 6, "EXTREME")).toBe(false);
    expect(canActivateThisFrame(8, 8, 6, "HEAVY")).toBe(false);
    expect(canActivateThisFrame(2, 2, 6, "LIGHT")).toBe(true);
    expect(canActivateThisFrame(0, 8, 0, "LIGHT")).toBe(false);
  });

  it("prioritizes near-target and frustum assets over distant heavy ones", () => {
    const near = scoreActivationPriority({
      distanceM: 80,
      inFrustum: true,
      nearTarget: true,
      manifestPriority: true,
      heavyClass: "LIGHT",
    });
    const farHeavy = scoreActivationPriority({
      distanceM: 2400,
      inFrustum: false,
      nearTarget: false,
      manifestPriority: false,
      heavyClass: "EXTREME",
    });
    expect(near).toBeLessThan(farHeavy);
  });
});

describe("ProgressiveSceneActivator", () => {
  it("rejects duplicate ingest of the same parsed root", () => {
    const act = new ProgressiveSceneActivator();
    const asset = stubAsset("TILE_A");
    expect(act.ingest(asset)).toBe(true);
    expect(act.ingest(asset)).toBe(false);
    expect(act.pendingCount()).toBe(1);
    act.disposeAll();
  });

  it("activates the nearest HEAVY asset first and not a second HEAVY in the same frame", () => {
    const act = new ProgressiveSceneActivator();
    const near = stubAsset("NEAR", {
      triangleCount: 600_000,
      heavyClass: "HEAVY",
      bounds: { minX: -10, maxX: 10, minZ: -10, maxZ: 10 },
    });
    const far = stubAsset("FAR", {
      triangleCount: 600_000,
      heavyClass: "HEAVY",
      bounds: { minX: 4000, maxX: 4020, minZ: 4000, maxZ: 4020 },
    });
    expect(act.ingest(near)).toBe(true);
    expect(act.ingest(far)).toBe(true);
    const attached: string[] = [];
    act.tick(tickCtx(), (info) => attached.push(info.asset.id));
    expect(attached).toEqual(["NEAR"]);
    expect(act.activatedCount()).toBe(1);
    expect(act.pendingCount()).toBe(1);
    act.disposeAll();
  });

  it("does not activate while INTERACTING", () => {
    const act = new ProgressiveSceneActivator();
    act.ingest(stubAsset("WAIT"));
    const attached: string[] = [];
    act.tick(tickCtx({ mode: "INTERACTING" }), (info) => attached.push(info.asset.id));
    expect(attached).toEqual([]);
    expect(act.pendingCount()).toBe(1);
    act.disposeAll();
  });

  it("skips EXTREME activation during SETTLING", () => {
    const act = new ProgressiveSceneActivator();
    act.ingest(stubAsset("XL", { triangleCount: 2_000_000, heavyClass: "EXTREME" }));
    const attached: string[] = [];
    act.tick(tickCtx({ mode: "SETTLING" }), (info) => attached.push(info.asset.id));
    expect(attached).toEqual([]);
    act.disposeAll();
  });

  it("disposes parsed-but-not-active assets on cancel", () => {
    const act = new ProgressiveSceneActivator();
    const asset = stubAsset("PENDING");
    const geo = (asset.object3D!.children[0] as THREE.Mesh).geometry;
    act.ingest(asset);
    act.discard("PENDING");
    expect(act.pendingCount()).toBe(0);
    expect(act.isActivated("PENDING")).toBe(false);
    expect(geo.uuid).toBeTruthy();
    act.disposeAll();
  });

  it("3D remount uses a fresh activator without duplicate activation", () => {
    const first = new ProgressiveSceneActivator();
    const a = stubAsset("TILE_02_00");
    expect(first.ingest(a)).toBe(true);
    first.disposeAll();
    const second = new ProgressiveSceneActivator();
    const b = stubAsset("TILE_02_00");
    expect(second.ingest(b)).toBe(true);
    expect(second.ingest(b)).toBe(false);
    expect(first.pendingCount()).toBe(0);
    expect(first.activatedCount()).toBe(0);
    second.disposeAll();
  });
});

describe("manifest bounds cache", () => {
  it("schedules from manifest bounds without measuring Box3 until requested", () => {
    const bounds = { minX: -10, maxX: 10, minZ: -4, maxZ: 6, minY: 0, maxY: 2 };
    const c = cacheManifestCenter("TILE_X", bounds);
    expect(c).toEqual({ x: 0, y: 1, z: 1 });
    expect(getCachedCenter("TILE_X")).toEqual(c);
    expect(getMeasuredBounds("TILE_X")).toBeUndefined();
    cacheMeasuredBounds("TILE_X", { minX: -1, maxX: 1, minZ: -1, maxZ: 1, minY: 0, maxY: 3 });
    expect(getMeasuredBounds("TILE_X")?.maxY).toBe(3);
    expect(getCachedCenter("TILE_X")).toEqual({ x: 0, y: 1.5, z: 0 });
  });
});

describe("Safari idle callback fallback", () => {
  it("falls back to setTimeout when requestIdleCallback is missing", () => {
    const origRic = (globalThis as { requestIdleCallback?: unknown }).requestIdleCallback;
    const origCancel = (globalThis as { cancelIdleCallback?: unknown }).cancelIdleCallback;
    Reflect.deleteProperty(globalThis, "requestIdleCallback");
    Reflect.deleteProperty(globalThis, "cancelIdleCallback");
    expect(hasRequestIdleCallback()).toBe(false);
    vi.useFakeTimers();
    let remaining = -1;
    const handle = scheduleIdleWork((deadline) => {
      remaining = deadline.timeRemaining();
    }, 1000);
    expect(remaining).toBe(-1);
    vi.advanceTimersByTime(16);
    expect(remaining).toBe(2);
    handle.cancel();
    if (typeof origRic === "function") {
      (globalThis as { requestIdleCallback: typeof origRic }).requestIdleCallback = origRic;
    }
    if (typeof origCancel === "function") {
      (globalThis as { cancelIdleCallback: typeof origCancel }).cancelIdleCallback = origCancel;
    }
  });
});

describe("registry in-place lifecycle + 2D/3D cleanup", () => {
  it("mutates the same CityAsset instance on update (no duplicate scene records)", () => {
    const reg = new AssetRegistry();
    const row = reg.register({ id: "t", url: "/assets/odessa/t.glb" });
    const updated = reg.update("t", { lifecycle: "queued", status: "queued" });
    expect(updated).toBe(row);
    expect(row.lifecycle).toBe("queued");
    expect(reg.list()).toHaveLength(1);
  });

  it("2D → 3D → 2D view-mode roundtrip plus activator dispose leaves no pending graphs", () => {
    writeViewMode("2d");
    expect(readViewMode()).toBe("2d");
    writeViewMode("3d");
    const act = new ProgressiveSceneActivator();
    act.ingest(stubAsset("LIVE"));
    expect(act.pendingCount()).toBe(1);
    act.disposeAll();
    clearBoundsCache();
    writeViewMode("2d");
    expect(readViewMode()).toBe("2d");
    expect(act.pendingCount()).toBe(0);
    expect(act.activatedCount()).toBe(0);
  });
});
