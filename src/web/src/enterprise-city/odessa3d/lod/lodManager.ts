/**
 * Per-frame-budget LOD evaluator. Uses manifest bounds cache only — no Box3.
 */

import type { QualityProfile } from "../types";
import type { DistanceTier, LodDecision, LodDiagnostics, LodThresholds } from "./lodTypes";
import { lodThresholdsFor, radiusFromBounds } from "./lodThresholds";
import { isScreenImportant, isSeaOrCoastProtected, scoreLodPriority, screenSpaceImportance } from "./lodScore";
import { classifyDistanceTierHysteresis, shouldAssetBeVisible } from "./lodVisibility";
import { getCachedCenter } from "../assetBoundsCache";
import { distanceXZ } from "../assetBoundsCache";

export type LodEvalAsset = {
  id: string;
  url?: string;
  layerId?: string;
  tileId?: string;
  bounds?: { minX: number; maxX: number; minZ: number; maxZ: number };
  sizeMb?: number;
  triangleCount?: number;
  currentlyVisible: boolean;
};

export type LodEvalContext = {
  camX: number;
  camZ: number;
  targetX: number;
  targetZ: number;
  inFrustum: (x: number, y: number, z: number, radius: number) => boolean;
  fovYDeg: number;
  viewportHeight: number;
  profile: QualityProfile;
  cityDiagonalM: number;
  lodBias: number;
  now?: number;
  waitMsFor?: (id: string) => number;
  priorityIds?: Set<string>;
};

const EMPTY_DIAG: LodDiagnostics = {
  near: 0,
  mid: 0,
  far: 0,
  cull: 0,
  visible: 0,
  hidden: 0,
  protectedSea: 0,
  protectedTarget: 0,
  activeTriangles: 0,
  hiddenTriangles: 0,
  priorityMs: 0,
  boundsMs: 0,
  transitionsPerSec: 0,
};

export class LodVisibilityManager {
  private prevTier = new Map<string, DistanceTier>();
  private last: LodDiagnostics = { ...EMPTY_DIAG };
  private thresholds: LodThresholds = lodThresholdsFor("medium");
  private transitionTimes: number[] = [];

  getThresholds() {
    return this.thresholds;
  }

  diagnostics(): LodDiagnostics {
    return this.last;
  }

  dispose() {
    this.prevTier.clear();
    this.transitionTimes = [];
    this.last = { ...EMPTY_DIAG };
  }

  evaluate(assets: readonly LodEvalAsset[], ctx: LodEvalContext): LodDecision[] {
    const tBounds = performance.now();
    this.thresholds = lodThresholdsFor(ctx.profile, ctx.cityDiagonalM, ctx.lodBias);
    const t = this.thresholds;
    const boundsMs = performance.now() - tBounds;

    const tPri = performance.now();
    const diag: LodDiagnostics = { ...EMPTY_DIAG, boundsMs };
    const out: LodDecision[] = [];

    for (const asset of assets) {
      const c = getCachedCenter(asset.id);
      const x = c?.x ?? 0;
      const y = c?.y ?? 0;
      const z = c?.z ?? 0;
      const dist = distanceXZ(ctx.camX, ctx.camZ, x, z);
      const toTarget = distanceXZ(ctx.targetX, ctx.targetZ, x, z);
      const radius = radiusFromBounds(asset.bounds);
      const inFrustum = ctx.inFrustum(x, y, z, radius);
      const nearTarget = toTarget < t.targetProtectM;
      const seaProtected = isSeaOrCoastProtected(asset.id, asset.layerId, asset.url);
      const ss = screenSpaceImportance(radius, dist, ctx.fovYDeg, ctx.viewportHeight);
      const screenImportant = isScreenImportant(ss, t.screenImportant);
      const prev = this.prevTier.get(asset.id);
      const tier = classifyDistanceTierHysteresis(dist, t, prev);
      this.prevTier.set(asset.id, tier);
      const visible = shouldAssetBeVisible(
        {
          id: asset.id,
          layerId: asset.layerId || "city",
          distanceM: dist,
          inFrustum,
          nearTarget,
          seaProtected,
          screenImportant,
          currentlyVisible: asset.currentlyVisible,
          prevTier: prev,
          triangleCount: asset.triangleCount,
        },
        t,
      );
      const score = scoreLodPriority({
        id: asset.id,
        distanceM: dist,
        inFrustum,
        nearTarget,
        manifestPriority: !!(ctx.priorityIds?.has(asset.id) || ctx.priorityIds?.has(asset.tileId || "")),
        seaProtected,
        screenImportant,
        layerId: asset.layerId,
        sizeMb: asset.sizeMb,
        waitMs: ctx.waitMsFor?.(asset.id),
      });
      const tris = asset.triangleCount ?? 0;
      if (visible !== asset.currentlyVisible) {
        this.transitionTimes.push(ctx.now ?? performance.now());
      }
      out.push({
        id: asset.id,
        tier,
        visible,
        protected: seaProtected || nearTarget,
        score,
        triangleCount: tris,
      });
      diag[tier === "NEAR" ? "near" : tier === "MID" ? "mid" : tier === "FAR" ? "far" : "cull"] += 1;
      if (visible) {
        diag.visible += 1;
        diag.activeTriangles += tris;
      } else {
        diag.hidden += 1;
        diag.hiddenTriangles += tris;
      }
      if (seaProtected) diag.protectedSea += 1;
      if (nearTarget) diag.protectedTarget += 1;
    }

    diag.priorityMs = +(performance.now() - tPri).toFixed(3);
    diag.boundsMs = +boundsMs.toFixed(3);
    const now = ctx.now ?? performance.now();
    this.transitionTimes = this.transitionTimes.filter((t) => now - t < 1000);
    diag.transitionsPerSec = this.transitionTimes.length;
    this.last = diag;
    return out;
  }
}
