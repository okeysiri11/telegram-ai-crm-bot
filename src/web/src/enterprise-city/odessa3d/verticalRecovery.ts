/**
 * STEP 29.5 / 29.6 / 29.7 — Odessa vertical-scale recovery (selective).
 *
 * STEP 29.7 (docs/STEP_29_7_ODESSA_RUNTIME_SPIKE_FORENSICS.md): the Safari
 * needle forest survived 29.6 because the mixed unit domain also exists at
 * VERTEX level inside merged meshes — miniature (all-meters) buildings baked
 * into cm-domain vertex buffers with correct placement. Per-mesh AABBs cannot
 * see them. Welded connected-component analysis of the source GLBs generates
 * a per-mesh domain table (odessaVerticalDomains.generated.ts); meshes whose
 * buffers contain ground-standing needle features are left exactly as
 * authored ("skip-mixed-domain"). Additionally every applied correction is
 * verified against the FINAL WORLD height and reverted if it misses the
 * target or classifies as a runtime spike.
 *
 * Proven source defects (docs/STEP_29_5_ODESSA_VERTICAL_RECOVERY_RESULT.md,
 * docs/STEP_29_6_ODESSA_SELECTIVE_VERTICAL_RECOVERY.md):
 *
 * 1. The building pipeline authored horizontal axes in centimeters and the
 *    vertical axis in meters; the exporter's uniform 0.01 node scale converts
 *    X/Z correctly and flattens the vertical exactly 100× (47/47 measurable
 *    WEB_height_N meshes cluster at requiredFactor ≈ 100; none at ~1 or ~10).
 * 2. A second unit domain exists: some meshes (WEB_plane_N, a minority of
 *    WEB_building / WEB_height meshes) are authored fully in meters, so the
 *    0.01 scale is wrong on EVERY axis and their world footprint is < 2 m.
 *    Recovering only their vertical necessarily produces tall thin needles
 *    (the STEP 29.5 spike defect). Since X/Z are frozen, these meshes are
 *    left unchanged and reported as source anomalies.
 *
 * Selective rule (STEP 29.6):
 * - Encoded meshes (WEB_height_N): factor = encodedHeight / measured
 *   pre-recovery world height — the source data decides the factor (skip if
 *   already ≈1). Applied only when the world footprint is plausible (≥ 2 m).
 * - Building-family meshes (WEB_build / HEAVY_BUILDING_CHUNK): the proven
 *   pipeline factor ×100, only when flattened (h ≤ 3 m) and footprint ≥ 2 m.
 * - Everything else (planes, rivers, roads, water, landuse, labels, base,
 *   unknown): NOT recovered — no objective unit-domain evidence.
 *
 * The correction conjugates the mesh local matrix with a world-space Y-only
 * scale about the world ground plane y=0 (the export's own scaling origin, so
 * building bases do not move):
 *
 *   local' = parentWorld⁻¹ · diag(1, factor, 1) · parentWorld · local
 *
 * No vertex is rewritten, no source file modified, world X/Z mathematically
 * unchanged; idempotent (userData guard) and reversible (original node TRS is
 * never touched).
 */

import * as THREE from "three";
import { isGroundDecalBox } from "./renderDebugTools";
import { ODESSA_VERTICAL_DOMAIN_VERDICTS } from "./odessaVerticalDomains.generated";

export type VerticalRecoveryMode = "off" | "selective" | "legacy";

/** One switch for the whole recovery. "selective" is the production mode;
 * "legacy" is the broad STEP 29.5 rule kept only for dev A/B comparison. */
export const ODESSA_VERTICAL_RECOVERY_MODE: VerticalRecoveryMode = "selective";

/** Proven building-pipeline defect factor (Phase 2: 47/47 cluster at ~100). */
export const ODESSA_VERTICAL_RECOVERY_FACTOR = 100;

/** Meshes taller than this cannot come from the flattened building export. */
const ALREADY_CORRECT_HEIGHT_M = 3;

/** Sanity ceiling — nothing in Odessa should exceed this after recovery. */
const MAX_RECOVERED_HEIGHT_M = 500;

/** World footprints below this are not in the cm-domain (no real building has
 * a sub-2 m footprint) → all-meters source anomaly → recovery would create a
 * needle → skip. */
const MIN_PLAUSIBLE_FOOTPRINT_M = 2;

/** Encoded factor ranges: ≈1 → already correct; beyond MAX → broken encode. */
const FACTOR_ALREADY_CORRECT_TOLERANCE = 0.05;
const MAX_SELECTIVE_FACTOR = 150;
const MIN_SELECTIVE_FACTOR = 0.5;

export type VerticalRecoveryReason = "encoded-height" | "building-family" | "legacy-band";

/** STEP 29.7 Phase 5 — permanent per-mesh marker. Version bumps invalidate nothing
 * at runtime (fresh parses always start unmarked); the marker's job is to make
 * double application impossible and reversal exact. */
export const VERTICAL_RECOVERY_VERSION = 2;

export type MeshRecoveryTag = {
  version: number;
  applied: boolean;
  factor: number;
  /** Local matrix before recovery — exact reversal source. */
  originalMatrix: number[];
  /** Pre-recovery FINAL WORLD height (not local). */
  sourceHeight: number;
  /** Target FINAL WORLD height the correction must produce. */
  expectedHeight: number;
  reason: VerticalRecoveryReason;
  /* kept for inspector compatibility */
  preHeight: number;
  postHeight: number;
};

export type RuntimeSpikeKind =
  | "SPIKE" // h > 15 m and (footprint < 2 m or h/footprint > 8)
  | "TALL_THIN" // h > 50 m and footprint < 5 m
  | "ZERO_FOOTPRINT"; // h > 15 m with near-zero footprint

/**
 * STEP 29.7 Phase 2 — runtime spike classifier over FINAL world boxes.
 * Returns null for healthy geometry.
 */
export function classifyRuntimeSpike(worldBox: THREE.Box3): RuntimeSpikeKind | null {
  const h = worldBox.max.y - worldBox.min.y;
  const foot = Math.max(worldBox.max.x - worldBox.min.x, worldBox.max.z - worldBox.min.z);
  if (h > 15 && foot < 0.05) return "ZERO_FOOTPRINT";
  if (h > 50 && foot < 5) return "TALL_THIN";
  if (h > 15 && (foot < 2 || h / Math.max(foot, 0.01) > 8)) return "SPIKE";
  return null;
}

export type VerticalRecoveryResult = {
  mode: VerticalRecoveryMode;
  correctedMeshes: number;
  factorExact: number; // encoded-height meshes, per-mesh measured factor
  factorPipeline: number; // building-family meshes, proven ×100
  factorAlreadyCorrect: number; // encoded meshes measured at ≈1 → untouched
  skippedDecalBand: number;
  skippedAlreadyTall: number;
  skippedNeedleGuard: number; // all-meters unit-domain anomalies (spike guard)
  skippedMixedDomain: number; // STEP 29.7: vertex buffer bakes miniature m-domain features
  skippedNoEvidence: number; // no name evidence for the unit domain
  skippedBrokenEncode: number; // encoded factor outside sane range
  /** STEP 29.7 post-checks: corrections reverted because the FINAL WORLD
   * result missed the encoded height (>1 %) or classified as a runtime spike. */
  revertedHeightMismatch: number;
  revertedSpikePostCheck: number;
};

const scratchBox = new THREE.Box3();
const scratchParent = new THREE.Matrix4();
const scratchInv = new THREE.Matrix4();
const scratchScale = new THREE.Matrix4();
const scratchLocal = new THREE.Matrix4();
const IDENTITY = new THREE.Matrix4();

/** WEB_height_95 → 95 ; WEB_height_2_5 → 2.5 ; WEB_height_3_m → 3. */
export function parseEncodedHeight(name: string): number | null {
  const m = name.match(/height_(\d+)(?:_(\d+))?/i);
  if (!m) return null;
  const v = Number(m[2] != null && /^\d+$/.test(m[2]) ? `${m[1]}.${m[2]}` : m[1]);
  return Number.isFinite(v) && v > 0 ? v : null;
}

/** The building pipeline proven to be cm-horizontal/m-vertical (×100). */
export function isBuildingFamilyName(name: string): boolean {
  return /(^|_)build/i.test(name) || /^HEAVY_BUILDING_CHUNK/i.test(name);
}

function meshWorldBox(mesh: THREE.Mesh): THREE.Box3 | null {
  const geo = mesh.geometry;
  if (!geo) return null;
  if (!geo.boundingBox) geo.computeBoundingBox();
  if (!geo.boundingBox) return null;
  return scratchBox.copy(geo.boundingBox).applyMatrix4(mesh.matrixWorld);
}

function applyWorldYScale(mesh: THREE.Mesh, factor: number) {
  scratchParent.copy(mesh.parent ? mesh.parent.matrixWorld : IDENTITY);
  scratchInv.copy(scratchParent).invert();
  scratchScale.makeScale(1, factor, 1);
  scratchLocal.copy(mesh.matrix);
  mesh.matrix.copy(scratchInv).multiply(scratchScale).multiply(scratchParent).multiply(scratchLocal);
  mesh.matrixAutoUpdate = false;
  mesh.matrixWorldNeedsUpdate = true;
}

type Decision =
  | { kind: "apply"; factor: number; reason: VerticalRecoveryReason }
  | {
      kind:
        | "decal-band"
        | "already-tall"
        | "already-correct"
        | "needle-guard"
        | "mixed-domain"
        | "no-evidence"
        | "broken-encode";
    };

/**
 * STEP 29.7/29.8 — per-mesh vertex-domain verdict from the generated table
 * (welded connected-component analysis of the source GLBs). Merged meshes
 * whose vertex buffers bake meter-domain miniature buildings would sprout
 * ground-standing needles under any whole-mesh vertical recovery — the
 * per-mesh AABB cannot see them (this is exactly why STEP 29.6 reported
 * zero spikes offline while Safari still rendered a needle forest).
 * "repair-components" meshes are excluded here and handed to the STEP 29.8
 * component-level repair (componentRepair.ts) instead.
 */
function domainVerdict(mesh: THREE.Mesh): "recover" | "repair-components" | "unknown" {
  const pos = mesh.geometry?.getAttribute("position");
  if (!pos) return "unknown";
  return ODESSA_VERTICAL_DOMAIN_VERDICTS[`${mesh.name}|${pos.count}`] ?? "unknown";
}

function decide(mesh: THREE.Mesh, box: THREE.Box3, mode: VerticalRecoveryMode): Decision {
  const h = box.max.y - box.min.y;
  const footprint = Math.max(box.max.x - box.min.x, box.max.z - box.min.z);

  if (isGroundDecalBox(box)) return { kind: "decal-band" };

  if (mode === "legacy") {
    /* STEP 29.5 broad rule — dev comparison only. */
    if (h > ALREADY_CORRECT_HEIGHT_M || h * ODESSA_VERTICAL_RECOVERY_FACTOR > MAX_RECOVERED_HEIGHT_M) {
      return { kind: "already-tall" };
    }
    return { kind: "apply", factor: ODESSA_VERTICAL_RECOVERY_FACTOR, reason: "legacy-band" };
  }

  const encoded = parseEncodedHeight(mesh.name);
  if (encoded != null) {
    if (h < 1e-4) return { kind: "broken-encode" }; // flat polygon carrying a height name
    const factor = encoded / h;
    if (Math.abs(factor - 1) <= FACTOR_ALREADY_CORRECT_TOLERANCE) return { kind: "already-correct" };
    if (factor > MAX_SELECTIVE_FACTOR || factor < MIN_SELECTIVE_FACTOR) return { kind: "broken-encode" };
    if (footprint < MIN_PLAUSIBLE_FOOTPRINT_M) return { kind: "needle-guard" };
    if (encoded > MAX_RECOVERED_HEIGHT_M) return { kind: "broken-encode" };
    if (domainVerdict(mesh) === "repair-components") return { kind: "mixed-domain" };
    return { kind: "apply", factor, reason: "encoded-height" };
  }

  if (isBuildingFamilyName(mesh.name)) {
    if (h > ALREADY_CORRECT_HEIGHT_M) return { kind: "already-tall" };
    if (footprint < MIN_PLAUSIBLE_FOOTPRINT_M) return { kind: "needle-guard" };
    if (h * ODESSA_VERTICAL_RECOVERY_FACTOR > MAX_RECOVERED_HEIGHT_M) return { kind: "already-tall" };
    if (domainVerdict(mesh) === "repair-components") return { kind: "mixed-domain" };
    return { kind: "apply", factor: ODESSA_VERTICAL_RECOVERY_FACTOR, reason: "building-family" };
  }

  return { kind: "no-evidence" };
}

export function applyOdessaVerticalScaleRecovery(
  root: THREE.Object3D,
  mode: VerticalRecoveryMode = ODESSA_VERTICAL_RECOVERY_MODE,
): VerticalRecoveryResult {
  const result: VerticalRecoveryResult = {
    mode,
    correctedMeshes: 0,
    factorExact: 0,
    factorPipeline: 0,
    factorAlreadyCorrect: 0,
    skippedDecalBand: 0,
    skippedAlreadyTall: 0,
    skippedNeedleGuard: 0,
    skippedMixedDomain: 0,
    skippedNoEvidence: 0,
    skippedBrokenEncode: 0,
    revertedHeightMismatch: 0,
    revertedSpikePostCheck: 0,
  };
  if (mode === "off") return result;
  root.updateMatrixWorld(true);

  const targets: Array<{ mesh: THREE.Mesh; factor: number; reason: VerticalRecoveryReason; preHeight: number }> = [];
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    /* Phase 5 idempotence: an applied marker means never touch again —
     * across tile reloads, LOD activation, remounts and mode reapplication. */
    if ((mesh.userData.odessaVerticalRecovery as MeshRecoveryTag | undefined)?.applied) return;
    if (mesh.userData.odessaVerticalRecovery) return;
    delete mesh.userData.odessaSpikeSuspect;
    delete mesh.userData.odessaMixedDomain;
    const box = meshWorldBox(mesh);
    if (!box) return;
    const decision = decide(mesh, box, mode);
    switch (decision.kind) {
      case "apply":
        targets.push({ mesh, factor: decision.factor, reason: decision.reason, preHeight: box.max.y - box.min.y });
        break;
      case "decal-band":
        result.skippedDecalBand += 1;
        break;
      case "already-tall":
        result.skippedAlreadyTall += 1;
        break;
      case "already-correct":
        result.factorAlreadyCorrect += 1;
        break;
      case "needle-guard":
        result.skippedNeedleGuard += 1;
        mesh.userData.odessaSpikeSuspect = true;
        break;
      case "mixed-domain":
        result.skippedMixedDomain += 1;
        mesh.userData.odessaMixedDomain = true;
        break;
      case "no-evidence":
        result.skippedNoEvidence += 1;
        break;
      case "broken-encode":
        result.skippedBrokenEncode += 1;
        break;
    }
  });

  for (const { mesh, factor, reason, preHeight } of targets) {
    const originalMatrix = mesh.matrix.toArray();
    const encoded = reason === "encoded-height" ? parseEncodedHeight(mesh.name) : null;
    const expectedHeight = encoded ?? preHeight * factor;
    applyWorldYScale(mesh, factor);

    /* STEP 29.7 Phase 6 — verify the FINAL WORLD height, not the local one.
     * The invariant is enforced where the transform is applied: if the world
     * result misses the target (unexpected parent scale, unforeseen runtime
     * state) or classifies as a runtime spike, the correction is reverted
     * and the mesh is flagged instead of shipping a needle. */
    mesh.updateWorldMatrix(true, false);
    const post = meshWorldBox(mesh);
    const postHeight = post ? post.max.y - post.min.y : NaN;
    const heightOk =
      post != null &&
      Number.isFinite(postHeight) &&
      Math.abs(postHeight - expectedHeight) / Math.max(expectedHeight, 1e-6) <= 0.01;
    const spikeKind = post ? classifyRuntimeSpike(post) : "ZERO_FOOTPRINT";

    if (!heightOk || spikeKind != null) {
      mesh.matrix.fromArray(originalMatrix);
      mesh.matrix.decompose(mesh.position, mesh.quaternion, mesh.scale);
      mesh.matrixAutoUpdate = true;
      mesh.matrixWorldNeedsUpdate = true;
      mesh.userData.odessaSpikeSuspect = true;
      if (!heightOk) result.revertedHeightMismatch += 1;
      else result.revertedSpikePostCheck += 1;
      continue;
    }

    const tag: MeshRecoveryTag = {
      version: VERTICAL_RECOVERY_VERSION,
      applied: true,
      factor,
      originalMatrix,
      sourceHeight: preHeight,
      expectedHeight,
      reason,
      preHeight,
      postHeight,
    };
    mesh.userData.odessaVerticalRecovery = tag;
    result.correctedMeshes += 1;
    if (reason === "encoded-height") result.factorExact += 1;
    else result.factorPipeline += 1;
  }

  root.updateMatrixWorld(true);
  return result;
}

export function emptyVerticalRecoveryResult(mode: VerticalRecoveryMode = "off"): VerticalRecoveryResult {
  return {
    mode,
    correctedMeshes: 0,
    factorExact: 0,
    factorPipeline: 0,
    factorAlreadyCorrect: 0,
    skippedDecalBand: 0,
    skippedAlreadyTall: 0,
    skippedNeedleGuard: 0,
    skippedMixedDomain: 0,
    skippedNoEvidence: 0,
    skippedBrokenEncode: 0,
    revertedHeightMismatch: 0,
    revertedSpikePostCheck: 0,
  };
}

/** Full revert — restores the exact pre-recovery local matrix stored in the marker
 * (falls back to recomposing the untouched node TRS for markers without one). */
export function revertOdessaVerticalScaleRecovery(root: THREE.Object3D): number {
  let reverted = 0;
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    delete mesh.userData.odessaSpikeSuspect;
    delete mesh.userData.odessaMixedDomain;
    const tag = mesh.userData.odessaVerticalRecovery as MeshRecoveryTag | undefined;
    if (!tag) return;
    delete mesh.userData.odessaVerticalRecovery;
    if (Array.isArray(tag.originalMatrix) && tag.originalMatrix.length === 16) {
      mesh.matrix.fromArray(tag.originalMatrix);
      mesh.matrix.decompose(mesh.position, mesh.quaternion, mesh.scale);
    }
    mesh.matrixAutoUpdate = true;
    mesh.updateMatrix();
    mesh.matrixWorldNeedsUpdate = true;
    reverted += 1;
  });
  root.updateMatrixWorld(true);
  return reverted;
}

export function countVerticalRecoveredMeshes(root: THREE.Object3D): number {
  let n = 0;
  root.traverse((obj) => {
    if ((obj as THREE.Mesh).isMesh && obj.userData.odessaVerticalRecovery) n += 1;
  });
  return n;
}
