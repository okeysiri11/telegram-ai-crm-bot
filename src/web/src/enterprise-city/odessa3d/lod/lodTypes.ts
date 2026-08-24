/**
 * Virtual LOD / visibility types. No extra GLB files — distance + importance only.
 */

import type { HeavyClass } from "../assetLifecycle";

export type DistanceTier = "NEAR" | "MID" | "FAR" | "CULL";

export type LodThresholds = {
  nearM: number;
  midM: number;
  farM: number;
  targetProtectM: number;
  screenImportant: number;
  hysteresis: number;
};

export type LodScoreInput = {
  id?: string;
  distanceM: number;
  inFrustum: boolean;
  nearTarget: boolean;
  manifestPriority: boolean;
  seaProtected: boolean;
  screenImportant: boolean;
  layerId?: string;
  heavyClass?: HeavyClass;
  sizeMb?: number;
  cameraForwardDot?: number;
  waitMs?: number;
};

export type LodVisibilityInput = {
  id: string;
  layerId: string;
  distanceM: number;
  inFrustum: boolean;
  nearTarget: boolean;
  seaProtected: boolean;
  screenImportant: boolean;
  currentlyVisible: boolean;
  prevTier?: DistanceTier;
  triangleCount?: number;
};

export type LodDecision = {
  id: string;
  tier: DistanceTier;
  visible: boolean;
  protected: boolean;
  score: number;
  triangleCount: number;
};

export type LodDiagnostics = {
  near: number;
  mid: number;
  far: number;
  cull: number;
  visible: number;
  hidden: number;
  protectedSea: number;
  protectedTarget: number;
  activeTriangles: number;
  hiddenTriangles: number;
  priorityMs: number;
  boundsMs: number;
  transitionsPerSec: number;
};
