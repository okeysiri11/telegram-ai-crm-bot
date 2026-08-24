/**
 * STEP 29.4 — artifact root-cause tooling.
 *
 * Fix (production): deterministic polygon-offset layering for the flat OSM
 * ground-decal stack contained in the source GLB (layers authored 1–5 mm
 * apart z-fight at oblique angles because depth precision at distance
 * exceeds the authored gaps). Geometry, colors, and georeference untouched —
 * polygonOffset biases only depth-buffer values.
 *
 * Diagnostics (dev only): true source-city isolation, wireframe/depth-debug/
 * side/transparency material overrides, binary mesh bisection, ALT+click
 * inspector, camera-altitude report.
 */

import * as THREE from "three";

import { componentClassAtFace } from "./componentRepair";

/* ------------------------------------------------------------------ */
/* Ground-decal depth layering (the STEP 29.4 fix)                      */
/* ------------------------------------------------------------------ */

/**
 * Authored decal band in the STEP 29.4 reference frame (legacy 1/100
 * package): flat meshes within ±60 mm of y=0, ≤20 mm thick. The STEP 29.9
 * metric package authors the identical stack ×100 (±6 m band, ≤2 m thick,
 * 0.1 m offsets), so every classifier takes the package `yScale`
 * (odessaPackage.decalYScale, default 1 = legacy).
 */
export const DECAL_MAX_HEIGHT = 0.02;
export const DECAL_BAND_Y = 0.06;

/** Deterministic rank from the authored Y offset (1 mm resolution at yScale 1). */
export function decalRankForY(centerY: number, yScale = 1): number {
  return Math.max(0, Math.min(14, Math.round((centerY / yScale + 0.006) * 1000)));
}

export function isGroundDecalBox(box: THREE.Box3, yScale = 1): boolean {
  const h = box.max.y - box.min.y;
  const centerY = (box.max.y + box.min.y) / 2;
  return h <= DECAL_MAX_HEIGHT * yScale && Math.abs(centerY) <= DECAL_BAND_Y * yScale;
}

export type DecalLayeringResult = {
  decalMeshes: number;
  rankedMaterials: number;
  clonedMaterials: number;
};

const tmpBox = new THREE.Box3();

function meshWorldBox(mesh: THREE.Mesh): THREE.Box3 | null {
  const geo = mesh.geometry;
  if (!geo) return null;
  if (!geo.boundingBox) geo.computeBoundingBox();
  if (!geo.boundingBox) return null;
  tmpBox.copy(geo.boundingBox).applyMatrix4(mesh.matrixWorld);
  return tmpBox;
}

function setDecalOffset(mat: THREE.Material, rank: number) {
  mat.polygonOffset = true;
  mat.polygonOffsetFactor = -rank;
  mat.polygonOffsetUnits = -rank * 2;
  mat.userData.odessaDecalRank = rank;
  mat.needsUpdate = true;
}

/**
 * Ranks every flat ground-decal mesh by its authored Y offset so the GPU
 * separates the coplanar OSM layers deterministically at every distance.
 * Shared materials used by non-decal meshes (or by decals of a different
 * rank) are cloned per rank so buildings/roads geometry is never biased.
 */
export function applyGroundDecalLayering(root: THREE.Object3D, yScale = 1): DecalLayeringResult {
  root.updateMatrixWorld(true);

  type Entry = { mesh: THREE.Mesh; rank: number };
  const decals: Entry[] = [];
  const materialRanks = new Map<THREE.Material, Set<number>>();
  const usedByNonDecal = new Set<THREE.Material>();

  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    const box = meshWorldBox(mesh);
    if (box && isGroundDecalBox(box, yScale)) {
      const rank = decalRankForY((box.max.y + box.min.y) / 2, yScale);
      decals.push({ mesh, rank });
      for (const m of mats) {
        if (!m) continue;
        if (!materialRanks.has(m)) materialRanks.set(m, new Set());
        materialRanks.get(m)!.add(rank);
      }
    } else {
      for (const m of mats) if (m) usedByNonDecal.add(m);
    }
  });

  const cloneCache = new Map<string, THREE.Material>();
  let cloned = 0;
  let ranked = 0;

  for (const { mesh, rank } of decals) {
    if (mesh.userData.odessaDecalApplied === rank) continue;
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    const next: THREE.Material[] = [];
    for (const m of mats) {
      if (!m) continue;
      const ranks = materialRanks.get(m);
      const exclusive = !usedByNonDecal.has(m) && ranks && ranks.size === 1;
      if (exclusive) {
        if (m.userData.odessaDecalRank !== rank) {
          setDecalOffset(m, rank);
          ranked += 1;
        }
        next.push(m);
      } else {
        const key = `${m.uuid}|${rank}`;
        let clone = cloneCache.get(key);
        if (!clone) {
          clone = m.clone();
          setDecalOffset(clone, rank);
          cloneCache.set(key, clone);
          cloned += 1;
        }
        next.push(clone);
      }
    }
    if (next.length) mesh.material = Array.isArray(mesh.material) ? next : next[0];
    mesh.userData.odessaDecalApplied = rank;
  }

  return { decalMeshes: decals.length, rankedMaterials: ranked, clonedMaterials: cloned };
}

/* ------------------------------------------------------------------ */
/* Dev material overrides (wireframe / side / transparency)             */
/* ------------------------------------------------------------------ */

export type DebugSideMode = "original" | "front" | "double";

export type DebugViewState = {
  sourceCityOnly: boolean;
  environmentOff: boolean;
  lightsNeutral: boolean;
  wireframe: boolean;
  depthDebug: boolean;
  sideMode: DebugSideMode;
  transparentOff: boolean;
  showMeshBounds: boolean;
  hideBasePlane: boolean;
  tightClip: boolean;
  /** STEP 29.6: show only meshes flagged as pathological spike geometry. */
  spikesOnly: boolean;
  /** STEP 29.7: hide every spike-suspect mesh. */
  hideSpikes: boolean;
  /** STEP 29.7: render spike-suspect meshes in flat red. */
  colorSpikesRed: boolean;
  /** STEP 29.8: vertex-color overlay — repaired components green, miniature
   * source anomalies red, uncertain yellow, unchanged gray. */
  componentColors: boolean;
  /** STEP 29.8: ORIGINAL / REPAIRED A/B — true reverts the vertex repair. */
  componentRepairOff: boolean;
};

export const DEFAULT_DEBUG_VIEW: DebugViewState = {
  sourceCityOnly: false,
  environmentOff: false,
  lightsNeutral: false,
  wireframe: false,
  depthDebug: false,
  sideMode: "original",
  transparentOff: false,
  showMeshBounds: false,
  hideBasePlane: false,
  tightClip: false,
  spikesOnly: false,
  hideSpikes: false,
  colorSpikesRed: false,
  componentColors: false,
  componentRepairOff: false,
};

type SavedMaterialProps = {
  wireframe: boolean;
  side: THREE.Side;
  transparent: boolean;
  opacity: number;
};

/** Snapshot/restore mutator for shared materials — dev toggles never leak. */
export class MaterialDebugOverride {
  private saved = new Map<THREE.Material, SavedMaterialProps>();

  apply(root: THREE.Object3D, state: Pick<DebugViewState, "wireframe" | "sideMode" | "transparentOff">) {
    const active = state.wireframe || state.sideMode !== "original" || state.transparentOff;
    if (!active) {
      this.restore();
      return;
    }
    root.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh) return;
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      for (const mat of mats) {
        if (!mat) continue;
        const std = mat as THREE.MeshStandardMaterial;
        if (!this.saved.has(mat)) {
          this.saved.set(mat, {
            wireframe: !!std.wireframe,
            side: mat.side,
            transparent: mat.transparent,
            opacity: mat.opacity,
          });
        }
        const orig = this.saved.get(mat)!;
        if ("wireframe" in std) std.wireframe = state.wireframe ? true : orig.wireframe;
        mat.side =
          state.sideMode === "front" ? THREE.FrontSide : state.sideMode === "double" ? THREE.DoubleSide : orig.side;
        if (state.transparentOff) {
          mat.transparent = false;
          mat.opacity = 1;
        } else {
          mat.transparent = orig.transparent;
          mat.opacity = orig.opacity;
        }
        mat.needsUpdate = true;
      }
    });
  }

  restore() {
    for (const [mat, orig] of this.saved) {
      const std = mat as THREE.MeshStandardMaterial;
      if ("wireframe" in std) std.wireframe = orig.wireframe;
      mat.side = orig.side;
      mat.transparent = orig.transparent;
      mat.opacity = orig.opacity;
      mat.needsUpdate = true;
    }
    this.saved.clear();
  }
}

export function createDepthDebugMaterial(): THREE.MeshDepthMaterial {
  const mat = new THREE.MeshDepthMaterial();
  mat.name = "odessaDepthDebug";
  return mat;
}

/* ------------------------------------------------------------------ */
/* STEP 29.7 — spike-suspect highlighter + runtime spike report         */
/* ------------------------------------------------------------------ */

/** Flat red override for spike-suspect meshes; original materials restored on release. */
export class SpikeHighlighter {
  private saved = new Map<THREE.Mesh, THREE.Material | THREE.Material[]>();
  private red = new THREE.MeshBasicMaterial({ color: 0xff2020, name: "odessaSpikeRed" });

  apply(root: THREE.Object3D, active: boolean) {
    if (!active) {
      this.restore();
      return;
    }
    root.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh || !mesh.userData.odessaSpikeSuspect) return;
      if (!this.saved.has(mesh)) this.saved.set(mesh, mesh.material);
      mesh.material = this.red;
    });
  }

  restore() {
    for (const [mesh, mat] of this.saved) mesh.material = mat;
    this.saved.clear();
  }

  dispose() {
    this.restore();
    this.red.dispose();
  }
}

export type RuntimeSpikeReportRow = {
  uuid: string;
  name: string;
  parentChain: string;
  visible: boolean;
  worldBox: { min: [number, number, number]; max: [number, number, number] };
  worldWidthX: number;
  worldDepthZ: number;
  worldHeightY: number;
  footprintMax: number;
  footprintMin: number;
  heightToFootprint: number;
  material: string;
  objectScale: [number, number, number];
  parentScales: Array<[number, number, number]>;
  matrixWorld: number[];
  determinant: number;
  encodedHeight: number | null;
  recovery: {
    factor: number;
    sourceHeight: number;
    expectedHeight: number;
    reason: string;
  } | null;
  spikeSuspect: boolean;
  mixedDomain: boolean;
  runtimeSpike: string | null;
};

/**
 * Phase 1/2 — measure the ACTUAL rendered scene (final matrixWorld) and
 * classify runtime spike suspects. Returns every mesh when `full`, otherwise
 * only flagged/spiking rows.
 */
export function collectRuntimeSpikeReport(root: THREE.Object3D, full = false): RuntimeSpikeReportRow[] {
  root.updateMatrixWorld(true);
  const rows: RuntimeSpikeReportRow[] = [];
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    const box = meshWorldBox(mesh);
    if (!box) return;
    const h = box.max.y - box.min.y;
    const wx = box.max.x - box.min.x;
    const wz = box.max.z - box.min.z;
    const footMax = Math.max(wx, wz);
    const foot = Math.max(footMax, 0.01);
    let spike: string | null = null;
    if (h > 15 && footMax < 0.05) spike = "ZERO_FOOTPRINT";
    else if (h > 50 && footMax < 5) spike = "TALL_THIN";
    else if (h > 15 && (footMax < 2 || h / foot > 8)) spike = "SPIKE";
    const flagged = !!mesh.userData.odessaSpikeSuspect || !!mesh.userData.odessaMixedDomain || spike != null;
    if (!full && !flagged) return;
    const chain: string[] = [];
    const parentScales: Array<[number, number, number]> = [];
    let p: THREE.Object3D | null = mesh.parent;
    while (p) {
      chain.unshift(p.name || p.type);
      parentScales.unshift([p.scale.x, p.scale.y, p.scale.z]);
      p = p.parent;
    }
    const mat = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
    const tag = mesh.userData.odessaVerticalRecovery as
      | { factor: number; sourceHeight?: number; preHeight: number; expectedHeight?: number; postHeight: number; reason: string }
      | undefined;
    const enc = mesh.name.match(/height_(\d+)(?:_(\d+))?/i);
    rows.push({
      uuid: mesh.uuid,
      name: mesh.name || "unnamed",
      parentChain: chain.join("/"),
      visible: mesh.visible,
      worldBox: {
        min: [+box.min.x.toFixed(3), +box.min.y.toFixed(3), +box.min.z.toFixed(3)],
        max: [+box.max.x.toFixed(3), +box.max.y.toFixed(3), +box.max.z.toFixed(3)],
      },
      worldWidthX: +wx.toFixed(3),
      worldDepthZ: +wz.toFixed(3),
      worldHeightY: +h.toFixed(3),
      footprintMax: +footMax.toFixed(3),
      footprintMin: +Math.min(wx, wz).toFixed(3),
      heightToFootprint: +(h / foot).toFixed(2),
      material: mat ? `${mat.name || "(unnamed)"} [${mat.type}]` : "(none)",
      objectScale: [mesh.scale.x, mesh.scale.y, mesh.scale.z],
      parentScales,
      matrixWorld: mesh.matrixWorld.toArray(),
      determinant: +mesh.matrixWorld.determinant().toFixed(6),
      encodedHeight: enc ? Number(enc[2] ? `${enc[1]}.${enc[2]}` : enc[1]) : null,
      recovery: tag
        ? {
            factor: +tag.factor.toFixed(4),
            sourceHeight: +(tag.sourceHeight ?? tag.preHeight).toFixed(4),
            expectedHeight: +(tag.expectedHeight ?? tag.postHeight).toFixed(2),
            reason: tag.reason,
          }
        : null,
      spikeSuspect: !!mesh.userData.odessaSpikeSuspect,
      mixedDomain: !!mesh.userData.odessaMixedDomain,
      runtimeSpike: spike,
    });
  });
  return rows;
}

/* ------------------------------------------------------------------ */
/* Phase 4 — binary mesh bisection                                      */
/* ------------------------------------------------------------------ */

export type BisectAction = "ALL" | "HALF_A" | "HALF_B" | "NEXT_SPLIT" | "RESET";

export type BisectStatus = {
  active: boolean;
  totalMeshes: number;
  currentCount: number;
  showing: "ALL" | "A" | "B";
  depth: number;
  path: string;
  currentNames: string[];
};

/**
 * Deterministic visibility bisector over the source-city meshes.
 * NEXT_SPLIT descends into the currently shown half; at ≤8 meshes the
 * remaining names are listed so the culprit can be read directly.
 */
export class MeshBisector {
  private meshes: THREE.Mesh[] = [];
  private savedVisible = new Map<THREE.Mesh, boolean>();
  private lo = 0;
  private hi = 0;
  private showing: "ALL" | "A" | "B" = "ALL";
  private path: string[] = [];
  private active = false;

  activate(root: THREE.Object3D) {
    if (this.active) return;
    this.meshes = [];
    root.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (mesh.isMesh) this.meshes.push(mesh);
    });
    this.meshes.sort((a, b) => (a.name + a.uuid).localeCompare(b.name + b.uuid));
    for (const m of this.meshes) this.savedVisible.set(m, m.visible);
    this.lo = 0;
    this.hi = this.meshes.length;
    this.showing = "ALL";
    this.path = [];
    this.active = true;
  }

  deactivate() {
    if (!this.active) return;
    for (const [m, v] of this.savedVisible) m.visible = v;
    this.savedVisible.clear();
    this.meshes = [];
    this.active = false;
    this.path = [];
    this.showing = "ALL";
  }

  isActive() {
    return this.active;
  }

  private currentRange(): [number, number] {
    const mid = Math.floor((this.lo + this.hi) / 2);
    if (this.showing === "A") return [this.lo, mid];
    if (this.showing === "B") return [mid, this.hi];
    return [this.lo, this.hi];
  }

  step(action: BisectAction) {
    if (!this.active) return;
    if (action === "RESET") {
      this.lo = 0;
      this.hi = this.meshes.length;
      this.showing = "ALL";
      this.path = [];
    } else if (action === "ALL") {
      this.showing = "ALL";
    } else if (action === "HALF_A") {
      this.showing = "A";
    } else if (action === "HALF_B") {
      this.showing = "B";
    } else if (action === "NEXT_SPLIT") {
      if (this.showing === "ALL") return;
      const [lo, hi] = this.currentRange();
      if (hi - lo <= 1) return;
      this.path.push(this.showing);
      this.lo = lo;
      this.hi = hi;
      this.showing = "ALL";
    }
    this.applyVisibility();
  }

  private applyVisibility() {
    const [lo, hi] = this.currentRange();
    for (let i = 0; i < this.meshes.length; i++) {
      this.meshes[i].visible = i >= lo && i < hi;
    }
  }

  status(): BisectStatus {
    const [lo, hi] = this.active ? this.currentRange() : [0, 0];
    const count = hi - lo;
    return {
      active: this.active,
      totalMeshes: this.meshes.length,
      currentCount: count,
      showing: this.showing,
      depth: this.path.length,
      path: this.path.join(">") || "-",
      currentNames:
        this.active && count > 0 && count <= 8
          ? this.meshes.slice(lo, hi).map((m) => `${m.name || "unnamed"} (${m.uuid.slice(0, 8)})`)
          : [],
    };
  }
}

/* ------------------------------------------------------------------ */
/* Phase 3 — click inspector                                            */
/* ------------------------------------------------------------------ */

export type InspectorHit = {
  object: string;
  parent: string;
  material: string;
  geometry: string;
  distance: number;
  worldPosition: [number, number, number];
  faceIndex: number;
  boundingBox: { min: [number, number, number]; max: [number, number, number] } | null;
  meshBoxHeight: number | null;
  meshFootprint: number | null;
  decalRank: number | null;
  /** STEP 29.6: vertical-recovery decision actually applied to this mesh. */
  verticalRecovery: { factor: number; preHeight: number; postHeight: number; reason: string } | null;
  spikeSuspect: boolean;
  /** STEP 29.7: mesh bakes miniature m-domain features — left as authored. */
  mixedDomain: boolean;
  /** STEP 29.8: component-level repair state at the picked face. */
  componentRepair: {
    meshTag: {
      totalComponents: number;
      repairedComponents: number;
      miniatureComponents: number;
      revertedComponents: number;
      modifiedVertices: number;
    } | null;
    hitClass: string | null;
    component: {
      id: number;
      vertices: number;
      preBox: { min: [number, number, number]; max: [number, number, number] };
      postBox: { min: [number, number, number]; max: [number, number, number] };
      pivotBaseY: number;
      scale: [number, number, number];
      finalWorldDimensions: [number, number, number];
    } | null;
  };
  /** STEP 29.7 Phase 4 — height through the full transform chain:
   * RAW geometry → each ancestor (with its local scale) → FINAL world. */
  transformChain: {
    rawGeometryHeight: number | null;
    localBox: { min: [number, number, number]; max: [number, number, number] } | null;
    objectScale: [number, number, number];
    ancestors: Array<{ name: string; scale: [number, number, number] }>;
    matrixWorld: number[];
    determinant: number;
    expectedWorldHeight: number | null;
    actualWorldHeight: number | null;
    codePath: string;
  };
};

export function describeIntersection(hit: THREE.Intersection): InspectorHit {
  const obj = hit.object as THREE.Mesh;
  const parts: string[] = [];
  const ancestors: Array<{ name: string; scale: [number, number, number] }> = [];
  let p: THREE.Object3D | null = obj.parent;
  while (p) {
    parts.unshift(p.name || p.type);
    ancestors.unshift({ name: p.name || p.type, scale: [p.scale.x, p.scale.y, p.scale.z] });
    p = p.parent;
  }
  const mat = Array.isArray(obj.material) ? obj.material[0] : obj.material;
  const box = obj.isMesh ? meshWorldBox(obj) : null;
  const localBox = obj.geometry?.boundingBox ?? null;
  const tag = obj.userData.odessaVerticalRecovery as
    | { factor: number; expectedHeight?: number; postHeight: number; reason: string }
    | undefined;
  const codePath = tag
    ? `verticalRecovery.applyOdessaVerticalScaleRecovery → decide:${tag.reason} → applyWorldYScale(×${(+tag.factor).toFixed(2)})`
    : obj.userData.odessaMixedDomain
      ? "verticalRecovery.decide → mixed-domain (domain table) → left as authored"
      : obj.userData.odessaSpikeSuspect
        ? "verticalRecovery.decide → needle-guard / post-check revert → left as authored"
        : "no recovery code path touched this mesh";
  return {
    object: obj.name || "unnamed",
    parent: parts.join("/") || "(scene)",
    material: mat ? `${mat.name || "(unnamed)"} [${mat.type}]` : "(none)",
    geometry: obj.geometry ? `${obj.geometry.type} uuid=${obj.geometry.uuid.slice(0, 8)}` : "(none)",
    distance: +hit.distance.toFixed(2),
    worldPosition: [+hit.point.x.toFixed(3), +hit.point.y.toFixed(3), +hit.point.z.toFixed(3)],
    faceIndex: hit.faceIndex ?? -1,
    boundingBox: box
      ? {
          min: [+box.min.x.toFixed(3), +box.min.y.toFixed(3), +box.min.z.toFixed(3)],
          max: [+box.max.x.toFixed(3), +box.max.y.toFixed(3), +box.max.z.toFixed(3)],
        }
      : null,
    meshBoxHeight: box ? +(box.max.y - box.min.y).toFixed(4) : null,
    meshFootprint: box ? +Math.max(box.max.x - box.min.x, box.max.z - box.min.z).toFixed(3) : null,
    decalRank: (mat?.userData?.odessaDecalRank as number | undefined) ?? null,
    verticalRecovery: obj.userData.odessaVerticalRecovery
      ? {
          factor: +(obj.userData.odessaVerticalRecovery.factor as number).toFixed(3),
          preHeight: +(obj.userData.odessaVerticalRecovery.preHeight as number).toFixed(4),
          postHeight: +(obj.userData.odessaVerticalRecovery.postHeight as number).toFixed(2),
          reason: String(obj.userData.odessaVerticalRecovery.reason),
        }
      : null,
    spikeSuspect: !!obj.userData.odessaSpikeSuspect,
    mixedDomain: !!obj.userData.odessaMixedDomain,
    componentRepair: describeComponentRepairAtHit(obj, hit.faceIndex ?? -1),
    transformChain: {
      rawGeometryHeight: localBox ? +(localBox.max.y - localBox.min.y).toFixed(4) : null,
      localBox: localBox
        ? {
            min: [+localBox.min.x.toFixed(3), +localBox.min.y.toFixed(3), +localBox.min.z.toFixed(3)],
            max: [+localBox.max.x.toFixed(3), +localBox.max.y.toFixed(3), +localBox.max.z.toFixed(3)],
          }
        : null,
      objectScale: [obj.scale.x, obj.scale.y, obj.scale.z],
      ancestors,
      matrixWorld: obj.matrixWorld.toArray().map((v) => +v.toFixed(6)),
      determinant: +obj.matrixWorld.determinant().toFixed(6),
      expectedWorldHeight: tag ? +((tag.expectedHeight ?? tag.postHeight) as number).toFixed(2) : null,
      actualWorldHeight: box ? +(box.max.y - box.min.y).toFixed(4) : null,
      codePath,
    },
  };
}

/** STEP 29.8 — per-component repair details for the ALT+click inspector. */
function describeComponentRepairAtHit(obj: THREE.Mesh, faceIndex: number): InspectorHit["componentRepair"] {
  const tag = obj.userData.odessaComponentRepair as
    | {
        totalComponents: number;
        repairedComponents: number;
        miniatureComponents: number;
        revertedComponents: number;
        modifiedVertices: number;
      }
    | undefined;
  const at = obj.isMesh && faceIndex >= 0 ? componentClassAtFace(obj, faceIndex) : null;
  return {
    meshTag: tag
      ? {
          totalComponents: tag.totalComponents,
          repairedComponents: tag.repairedComponents,
          miniatureComponents: tag.miniatureComponents,
          revertedComponents: tag.revertedComponents,
          modifiedVertices: tag.modifiedVertices,
        }
      : null,
    hitClass: at?.clsName ?? null,
    component: at?.componentInfo
      ? {
          ...at.componentInfo,
          finalWorldDimensions: [
            +(at.componentInfo.postBox.max[0] - at.componentInfo.postBox.min[0]).toFixed(3),
            +(at.componentInfo.postBox.max[1] - at.componentInfo.postBox.min[1]).toFixed(3),
            +(at.componentInfo.postBox.max[2] - at.componentInfo.postBox.min[2]).toFixed(3),
          ],
        }
      : null,
  };
}

/* ------------------------------------------------------------------ */
/* Phase 9 — camera-below-base report                                   */
/* ------------------------------------------------------------------ */

export type CameraAltitudeReport = {
  cameraY: number;
  cityBaseY: number;
  altitudeAboveBase: number;
  insideCityBox: boolean;
  belowCityBase: boolean;
  belowSeaLevel: boolean;
};

export function cameraAltitudeReport(camera: THREE.Camera, cityBox: THREE.Box3): CameraAltitudeReport {
  const pos = camera.position;
  return {
    cameraY: +pos.y.toFixed(2),
    cityBaseY: +cityBox.min.y.toFixed(3),
    altitudeAboveBase: +(pos.y - cityBox.min.y).toFixed(2),
    insideCityBox: cityBox.containsPoint(pos),
    belowCityBase: pos.y < cityBox.min.y,
    belowSeaLevel: pos.y < 0,
  };
}

/** Exact identity of the proven gray-slab base quad (Phase 3 evidence). */
export const BASE_PLANE_MESH_NAME = "WEB_base";

export function setBasePlaneHidden(root: THREE.Object3D, hidden: boolean): number {
  let count = 0;
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh || mesh.name !== BASE_PLANE_MESH_NAME) return;
    if (hidden) {
      if (mesh.visible) {
        mesh.userData.odessaBasePlaneHidden = true;
        mesh.visible = false;
      }
    } else if (mesh.userData.odessaBasePlaneHidden) {
      delete mesh.userData.odessaBasePlaneHidden;
      mesh.visible = true;
    }
    count += 1;
  });
  return count;
}
