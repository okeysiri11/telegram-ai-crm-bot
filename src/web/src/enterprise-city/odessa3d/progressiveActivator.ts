/**
 * Frame-budgeted activation of parsed GLB scenes.
 * Parsed roots stay off-scene until a RAF tick has budget.
 */

import * as THREE from "three";
import type { CityAsset } from "./types";
import {
  activationBudgetMs,
  canActivateThisFrame,
  classifyHeavyAsset,
  estimateActivationCostMs,
  transitionLifecycle,
  type HeavyClass,
} from "./assetLifecycle";
import type { RuntimePerfMode } from "./runtimePerfState";
import { cacheManifestCenter, distanceXZ, getCachedCenter } from "./assetBoundsCache";
import { prepareParsedScene } from "./scenePrep";
import { disposeObject3D } from "./disposeUtils";
import { scheduleIdleWork } from "./idleCallback";
import {
  emptyVisualPrepStats,
  mergeVisualPrepStats,
  type VisualPrepStats,
} from "./environment/buildingReadability";
import type { EnvironmentQuality } from "./environment/environmentPresets";
import {
  isSeaOrCoastProtected,
  isScreenImportant,
  radiusFromBounds,
  scoreLodPriority,
  screenSpaceImportance,
} from "./lod";

export type ActivatorAttachContext = {
  asset: CityAsset;
  root: THREE.Object3D;
  heavyClass: HeavyClass;
  triangleCount: number;
  objectCount: number;
  prepMs: number;
};

export type ActivatorTickContext = {
  now: number;
  mode: RuntimePerfMode;
  fps: number;
  camera: THREE.Camera;
  target: THREE.Vector3;
  frustum: THREE.Frustum;
  priorityIds: Set<string>;
  enableShadows: boolean;
  maxAnisotropy: number;
  environmentQuality?: EnvironmentQuality;
  fovYDeg?: number;
  viewportHeight?: number;
  nowMs?: number;
};

type Pending = {
  asset: CityAsset;
  root: THREE.Object3D;
  heavyClass: HeavyClass;
  prepared: boolean;
  triangleCount: number;
  objectCount: number;
  prepMs: number;
  ingestedAt: number;
};

export class ProgressiveSceneActivator {
  private pending = new Map<string, Pending>();
  private activated = new Set<string>();
  private idleHandle: { cancel: () => void } | null = null;
  private visualStats: VisualPrepStats = emptyVisualPrepStats();

  has(id: string): boolean {
    return this.pending.has(id) || this.activated.has(id);
  }

  isActivated(id: string): boolean {
    return this.activated.has(id);
  }

  pendingCount(): number {
    return this.pending.size;
  }

  activatedCount(): number {
    return this.activated.size;
  }

  visualPrepStats(): VisualPrepStats {
    return this.visualStats;
  }

  ingest(asset: CityAsset): boolean {
    if (!asset.object3D || this.has(asset.id)) return false;
    const root = asset.object3D;
    if (root.parent) return false;
    cacheManifestCenter(asset.id, asset.bounds);
    const heavyClass = classifyHeavyAsset({
      triangles: asset.triangleCount ?? asset.timings?.triangleCount,
      sizeMb: asset.sizeMb,
      layerId: asset.layerId,
    });
    this.pending.set(asset.id, {
      asset,
      root,
      heavyClass,
      prepared: false,
      triangleCount: asset.triangleCount ?? 0,
      objectCount: asset.objectCount ?? 0,
      prepMs: 0,
      ingestedAt: performance.now(),
    });
    return true;
  }

  tick(ctx: ActivatorTickContext, onAttach: (info: ActivatorAttachContext) => void): number {
    const budget = activationBudgetMs(ctx.mode, ctx.fps);
    if (budget <= 0 || this.pending.size === 0) return 0;

    const ordered = this.orderedPending(ctx);
    let spent = 0;
    let attached = 0;

    for (const item of ordered) {
      if (ctx.mode === "SETTLING" && (item.heavyClass === "HEAVY" || item.heavyClass === "EXTREME")) {
        continue;
      }
      const estimate = estimateActivationCostMs(item.heavyClass);
      if (!canActivateThisFrame(spent, estimate, budget, item.heavyClass)) break;

      const t0 = performance.now();
      if (!item.prepared) {
        this.prepareOne(item, ctx);
      }
      if (!item.prepared) continue;

      onAttach({
        asset: item.asset,
        root: item.root,
        heavyClass: item.heavyClass,
        triangleCount: item.triangleCount,
        objectCount: item.objectCount,
        prepMs: item.prepMs,
      });
      this.pending.delete(item.asset.id);
      this.activated.add(item.asset.id);
      attached += 1;
      spent += Math.max(performance.now() - t0, estimate * 0.25);
    }

    if (ctx.mode === "IDLE" && this.pending.size > 0) {
      this.scheduleIdlePrep(ctx);
    }
    return attached;
  }

  markDeactivated(id: string) {
    this.activated.delete(id);
  }

  /** Drop a parsed-but-not-active root. Does not dispose in-scene graphs. */
  discard(id: string) {
    const item = this.pending.get(id);
    if (item) {
      if (!item.root.parent) disposeObject3D(item.root);
      this.pending.delete(id);
    }
    this.activated.delete(id);
  }

  disposePending() {
    this.idleHandle?.cancel();
    this.idleHandle = null;
    for (const item of this.pending.values()) {
      if (!item.root.parent) disposeObject3D(item.root);
    }
    this.pending.clear();
  }

  disposeAll() {
    this.disposePending();
    this.activated.clear();
    this.visualStats = emptyVisualPrepStats();
  }

  private prepareOne(item: Pending, ctx: ActivatorTickContext) {
    const t0 = performance.now();
    item.asset.lifecycle = transitionLifecycle(item.asset.lifecycle || "parsed", "preparing");
    const info = prepareParsedScene(item.root, {
      enableShadows: ctx.enableShadows,
      maxAnisotropy: ctx.maxAnisotropy,
      assetId: item.asset.id,
      environmentQuality: ctx.environmentQuality ?? "medium",
    });
    mergeVisualPrepStats(this.visualStats, info.visual);
    item.triangleCount = info.triangleCount || item.triangleCount;
    item.objectCount = info.objectCount || item.objectCount;
    item.heavyClass = classifyHeavyAsset({
      triangles: item.triangleCount,
      sizeMb: item.asset.sizeMb,
      layerId: item.asset.layerId,
    });
    item.prepared = true;
    item.prepMs = performance.now() - t0;
    item.asset.lifecycle = transitionLifecycle("preparing", "ready");
    item.asset.triangleCount = item.triangleCount;
    item.asset.objectCount = item.objectCount;
    item.asset.heavyClass = item.heavyClass;
  }

  private scheduleIdlePrep(ctx: ActivatorTickContext) {
    if (this.idleHandle) return;
    this.idleHandle = scheduleIdleWork((deadline) => {
      this.idleHandle = null;
      if (deadline.timeRemaining() < 1) return;
      const next = this.orderedPending(ctx).find((p) => !p.prepared);
      if (!next) return;
      this.prepareOne(next, ctx);
    }, 1200);
  }

  private orderedPending(ctx: ActivatorTickContext): Pending[] {
    const cam = ctx.camera.position;
    const target = ctx.target;
    const rows = [...this.pending.values()];
    rows.sort((a, b) => this.score(a, cam, target, ctx) - this.score(b, cam, target, ctx));
    return rows;
  }

  private score(item: Pending, cam: THREE.Vector3, target: THREE.Vector3, ctx: ActivatorTickContext): number {
    const c = getCachedCenter(item.asset.id) ?? { x: 0, y: 0, z: 0 };
    const dist = distanceXZ(cam.x, cam.z, c.x, c.z);
    const toTarget = distanceXZ(target.x, target.z, c.x, c.z);
    const radius = radiusFromBounds(item.asset.bounds);
    const sphere = new THREE.Sphere(new THREE.Vector3(c.x, c.y, c.z), radius);
    const inFrustum = ctx.frustum.intersectsSphere(sphere);
    const ss = screenSpaceImportance(radius, dist, ctx.fovYDeg ?? 50, ctx.viewportHeight ?? 520);
    return scoreLodPriority({
      id: item.asset.id,
      distanceM: dist,
      inFrustum,
      nearTarget: toTarget < 380,
      manifestPriority: ctx.priorityIds.has(item.asset.id) || ctx.priorityIds.has(item.asset.tileId || ""),
      seaProtected: isSeaOrCoastProtected(item.asset.id, item.asset.layerId, item.asset.url),
      screenImportant: isScreenImportant(ss, 0.08),
      layerId: item.asset.layerId,
      heavyClass: item.heavyClass,
      sizeMb: item.asset.sizeMb,
      waitMs: Math.max(0, (ctx.nowMs ?? ctx.now) - item.ingestedAt),
    });
  }
}
