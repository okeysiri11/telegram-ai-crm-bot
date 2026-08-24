/**
 * STEP 29.8 — component-level geometry repair for merged Odessa meshes.
 *
 * Forensic context (docs/STEP_29_8_ODESSA_COMPONENT_GEOMETRY_REPAIR.md):
 * meshes with the generated verdict "repair-components" bake two vertex-level
 * unit domains into one buffer:
 *
 * 1. cm-domain FLATTENED buildings — correct footprints (≥ 2 m), heights
 *    crushed 100× by the exporter (the proven 29.5 pipeline defect). These
 *    ARE recoverable per component: a world-Y ×100 stretch about the
 *    component's own base grows them in place; X/Z stay bit-identical, so
 *    neighbors cannot overlap.
 * 2. all-meters MINIATURES — 1/100-scale buildings whose real-scale layout
 *    was destroyed at export (measured: nearest-neighbor spacing 0.2–0.6 m
 *    against intended 15–50 m footprints; agglomerations 25–77 m wide with
 *    3.5 m spacing). No affine transform about any pivot can reconstruct
 *    them without mass overlap, so they are SOURCE_ANOMALY: left
 *    bit-identical (microscopic, ≤ 0.25 m — never needles).
 *
 * The repair rewrites ONLY the vertices of proven class-1 components
 * (positions via a per-component conjugated matrix, normals via its
 * inverse-transpose). Indices, UVs, material groups and every other vertex
 * are untouched. Exact reversal backups and per-vertex class labels live in
 * a module WeakMap (not userData) so meshes stay clone/JSON-safe.
 */

import * as THREE from "three";

export const COMPONENT_REPAIR_VERSION = 1;

/** Proven cm-domain vertical flattening factor (STEP 29.5 Phase 1/2). */
export const COMPONENT_REPAIR_FACTOR = 100;

/* Phase 5 plausibility guards. */
const FLAT_MAX_H = 0.02; // ≤ 2 cm world: ground polygon / decal inside the mesh
const FLATTENED_MAX_H = 3; // crushed buildings measure ≤ 3 m pre-repair
const MIN_FOOT_SIDE = 2; // corrected buildings need width ≥ 2 m AND depth ≥ 2 m
const GROUND_BAND = 0.5; // repairable buildings stand on the ground
const MIN_REPAIRED_H = 2.5;
const MAX_REPAIRED_H = 250;
/** height / max(width, depth) guard — matches the runtime needle classifier
 * (ratio > 8 on a ground-standing feature reads as a spike), stricter than
 * the nominal Phase 5 "< 10" so no repaired component can classify as one. */
const MAX_ASPECT = 8;
const MINIATURE_MAX_FOOT = 1.5;
const MINIATURE_MIN_H = 0.025;

export const COMPONENT_CLASS = {
  UNCHANGED: 0,
  REPAIRED: 1,
  MINIATURE: 2, // SOURCE_ANOMALY — placement destroyed at export
  FLAT: 3,
  UNCERTAIN: 4,
  REVERTED_GUARD: 5, // failed post-repair plausibility → rolled back
} as const;

export type ComponentRepairTag = {
  version: number;
  applied: boolean;
  factor: number;
  totalComponents: number;
  repairedComponents: number;
  miniatureComponents: number;
  flatComponents: number;
  uncertainComponents: number;
  revertedComponents: number;
  modifiedVertices: number;
};

export type RepairedComponentInfo = {
  id: number;
  vertices: number;
  preBox: { min: [number, number, number]; max: [number, number, number] };
  postBox: { min: [number, number, number]; max: [number, number, number] };
  pivotBaseY: number;
  scale: [number, number, number];
};

type RepairData = {
  /** per-vertex class label (COMPONENT_CLASS values) */
  classes: Uint8Array;
  /** exact-reversal backup of modified vertices */
  backupIndex: Uint32Array;
  backupPos: Float32Array;
  backupNrm: Float32Array | null;
  repaired: RepairedComponentInfo[];
};

const repairStore = new WeakMap<THREE.Mesh, RepairData>();

export function getComponentRepairData(mesh: THREE.Mesh): RepairData | undefined {
  return repairStore.get(mesh);
}

/* ------------------------------------------------------------------ */
/* Connected components (index adjacency + position weld)               */
/* ------------------------------------------------------------------ */

type Decomposition = {
  /** root label per vertex (after path compression) */
  labels: Int32Array;
  /** world box per root label */
  boxes: Map<number, THREE.Box3>;
  /** vertex count per root label */
  counts: Map<number, number>;
};

/**
 * Phase 1 — decompose a merged geometry into connected components using
 * indexed triangle adjacency plus 1 mm-quantized position welding (merges
 * flat-shading duplicate vertices so a building is ONE component).
 */
export function decomposeGeometry(mesh: THREE.Mesh): Decomposition | null {
  const geo = mesh.geometry;
  const pos = geo?.getAttribute("position") as THREE.BufferAttribute | undefined;
  if (!pos) return null;
  const n = pos.count;
  const parent = new Int32Array(n);
  for (let i = 0; i < n; i++) parent[i] = i;
  const find = (a: number): number => {
    while (parent[a] !== a) {
      parent[a] = parent[parent[a]];
      a = parent[a];
    }
    return a;
  };
  const union = (a: number, b: number) => {
    const ra = find(a);
    const rb = find(b);
    if (ra !== rb) parent[rb] = ra;
  };

  const index = geo.getIndex();
  if (index) {
    for (let i = 0; i < index.count; i += 3) {
      const a = index.getX(i);
      union(a, index.getX(i + 1));
      union(a, index.getX(i + 2));
    }
  } else {
    for (let i = 0; i + 2 < n; i += 3) {
      union(i, i + 1);
      union(i, i + 2);
    }
  }

  /* position weld via integer spatial hash (exact-match buckets) */
  const buckets = new Map<number, number[]>();
  for (let i = 0; i < n; i++) {
    const qx = Math.round(pos.getX(i) * 1000);
    const qy = Math.round(pos.getY(i) * 1000);
    const qz = Math.round(pos.getZ(i) * 1000);
    const h = ((qx * 73856093) ^ (qy * 19349663) ^ (qz * 83492791)) | 0;
    const list = buckets.get(h);
    if (!list) {
      buckets.set(h, [i]);
      continue;
    }
    let welded = false;
    for (const j of list) {
      if (
        Math.round(pos.getX(j) * 1000) === qx &&
        Math.round(pos.getY(j) * 1000) === qy &&
        Math.round(pos.getZ(j) * 1000) === qz
      ) {
        union(j, i);
        welded = true;
        break;
      }
    }
    if (!welded) list.push(i);
  }

  const labels = new Int32Array(n);
  const boxes = new Map<number, THREE.Box3>();
  const counts = new Map<number, number>();
  const v = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    const r = find(i);
    labels[i] = r;
    let box = boxes.get(r);
    if (!box) {
      box = new THREE.Box3();
      boxes.set(r, box);
      counts.set(r, 0);
    }
    v.fromBufferAttribute(pos, i).applyMatrix4(mesh.matrixWorld);
    box.expandByPoint(v);
    counts.set(r, (counts.get(r) ?? 0) + 1);
  }
  return { labels, boxes, counts };
}

/* ------------------------------------------------------------------ */
/* Phase 2/3/4/5 — classify + repair + guards                           */
/* ------------------------------------------------------------------ */

type ComponentClass = (typeof COMPONENT_CLASS)[keyof typeof COMPONENT_CLASS];

function classifyComponent(box: THREE.Box3): ComponentClass {
  const h = box.max.y - box.min.y;
  const fx = box.max.x - box.min.x;
  const fz = box.max.z - box.min.z;
  const footMax = Math.max(fx, fz);
  const footMin = Math.min(fx, fz);
  if (h <= FLAT_MAX_H) return COMPONENT_CLASS.FLAT;
  if (
    footMin >= MIN_FOOT_SIDE &&
    h <= FLATTENED_MAX_H &&
    Math.abs(box.min.y) <= GROUND_BAND &&
    h * COMPONENT_REPAIR_FACTOR >= MIN_REPAIRED_H &&
    h * COMPONENT_REPAIR_FACTOR <= MAX_REPAIRED_H &&
    (h * COMPONENT_REPAIR_FACTOR) / Math.max(footMax, 0.01) < MAX_ASPECT
  ) {
    return COMPONENT_CLASS.REPAIRED;
  }
  if (footMax < MINIATURE_MAX_FOOT && h > MINIATURE_MIN_H && h <= FLATTENED_MAX_H) {
    return COMPONENT_CLASS.MINIATURE;
  }
  return COMPONENT_CLASS.UNCERTAIN;
}

/** Absolute post-repair needle guard (Phase 5). */
export function repairedBoxIsPathological(box: THREE.Box3): boolean {
  const h = box.max.y - box.min.y;
  const fx = box.max.x - box.min.x;
  const fz = box.max.z - box.min.z;
  const footMax = Math.max(fx, fz);
  const footMin = Math.min(fx, fz);
  if (footMin < 1 && h > 10) return true;
  if (h > MAX_REPAIRED_H || h < MIN_REPAIRED_H) return true;
  if (h / Math.max(footMax, 0.01) >= MAX_ASPECT) return true;
  return false;
}

export type ComponentRepairResult = ComponentRepairTag;

/**
 * Repairs the proven flattened cm-domain building components of one merged
 * mesh in place. Idempotent (userData marker); exactly reversible
 * (revertComponentRepair). Vertices of every other component stay
 * bit-identical; indices/UVs/groups are never touched.
 */
export function repairBuildingComponents(mesh: THREE.Mesh): ComponentRepairResult | null {
  const existing = mesh.userData.odessaComponentRepair as ComponentRepairTag | undefined;
  if (existing?.applied) return existing;

  const geo = mesh.geometry;
  const pos = geo?.getAttribute("position") as THREE.BufferAttribute | undefined;
  if (!pos) return null;
  mesh.updateWorldMatrix(true, false);
  const decomp = decomposeGeometry(mesh);
  if (!decomp) return null;

  const tag: ComponentRepairTag = {
    version: COMPONENT_REPAIR_VERSION,
    applied: true,
    factor: COMPONENT_REPAIR_FACTOR,
    totalComponents: decomp.boxes.size,
    repairedComponents: 0,
    miniatureComponents: 0,
    flatComponents: 0,
    uncertainComponents: 0,
    revertedComponents: 0,
    modifiedVertices: 0,
  };

  /* classify per component */
  const classByRoot = new Map<number, ComponentClass>();
  for (const [root, box] of decomp.boxes) {
    const cls = classifyComponent(box);
    classByRoot.set(root, cls);
    if (cls === COMPONENT_CLASS.MINIATURE) tag.miniatureComponents += 1;
    else if (cls === COMPONENT_CLASS.FLAT) tag.flatComponents += 1;
    else if (cls === COMPONENT_CLASS.UNCERTAIN) tag.uncertainComponents += 1;
  }

  const repairRoots = [...classByRoot.entries()].filter(([, c]) => c === COMPONENT_CLASS.REPAIRED).map(([r]) => r);
  const nrm = geo.getAttribute("normal") as THREE.BufferAttribute | undefined;

  if (repairRoots.length === 0) {
    /* nothing to modify — keep labels for dev tooling, no backups needed */
    const classes = new Uint8Array(pos.count);
    for (let i = 0; i < pos.count; i++) classes[i] = classByRoot.get(decomp.labels[i]) ?? COMPONENT_CLASS.UNCHANGED;
    repairStore.set(mesh, {
      classes,
      backupIndex: new Uint32Array(0),
      backupPos: new Float32Array(0),
      backupNrm: null,
      repaired: [],
    });
    mesh.userData.odessaComponentRepair = tag;
    return tag;
  }

  /* collect modified vertices + backups */
  const repairSet = new Set(repairRoots);
  const modified: number[] = [];
  for (let i = 0; i < pos.count; i++) {
    if (repairSet.has(decomp.labels[i])) modified.push(i);
  }
  const backupIndex = new Uint32Array(modified.length);
  const backupPos = new Float32Array(modified.length * 3);
  const backupNrm = nrm ? new Float32Array(modified.length * 3) : null;
  modified.forEach((vi, k) => {
    backupIndex[k] = vi;
    backupPos[k * 3] = pos.getX(vi);
    backupPos[k * 3 + 1] = pos.getY(vi);
    backupPos[k * 3 + 2] = pos.getZ(vi);
    if (nrm && backupNrm) {
      backupNrm[k * 3] = nrm.getX(vi);
      backupNrm[k * 3 + 1] = nrm.getY(vi);
      backupNrm[k * 3 + 2] = nrm.getZ(vi);
    }
  });

  /* per-component conjugated transform: local' = M⁻¹ · T(base) · S_y(f) · T(−base) · M */
  const world = mesh.matrixWorld;
  const worldInv = new THREE.Matrix4().copy(world).invert();
  const repairedInfo: RepairedComponentInfo[] = [];
  const vtx = new THREE.Vector3();
  const nvec = new THREE.Vector3();
  const local = new THREE.Matrix4();
  const normalMat = new THREE.Matrix3();
  const revertedRoots = new Set<number>();

  for (const root of repairRoots) {
    const preBox = decomp.boxes.get(root)!;
    const baseY = preBox.min.y;
    const stretch = new THREE.Matrix4()
      .makeTranslation(0, baseY, 0)
      .multiply(new THREE.Matrix4().makeScale(1, COMPONENT_REPAIR_FACTOR, 1))
      .multiply(new THREE.Matrix4().makeTranslation(0, -baseY, 0));
    local.copy(worldInv).multiply(stretch).multiply(world);
    normalMat.getNormalMatrix(local);

    const postBox = new THREE.Box3();
    for (const vi of modified) {
      if (decomp.labels[vi] !== root) continue;
      vtx.fromBufferAttribute(pos, vi).applyMatrix4(local);
      pos.setXYZ(vi, vtx.x, vtx.y, vtx.z);
      if (nrm) {
        nvec.fromBufferAttribute(nrm, vi).applyMatrix3(normalMat);
        if (nvec.lengthSq() > 1e-12) nvec.normalize();
        nrm.setXYZ(vi, nvec.x, nvec.y, nvec.z);
      }
      postBox.expandByPoint(vtx.clone().applyMatrix4(world));
    }

    if (repairedBoxIsPathological(postBox)) {
      /* Phase 5 rollback: revert ONLY this component, mark SOURCE_ANOMALY */
      for (let k = 0; k < backupIndex.length; k++) {
        const vi = backupIndex[k];
        if (decomp.labels[vi] !== root) continue;
        pos.setXYZ(vi, backupPos[k * 3], backupPos[k * 3 + 1], backupPos[k * 3 + 2]);
        if (nrm && backupNrm) nrm.setXYZ(vi, backupNrm[k * 3], backupNrm[k * 3 + 1], backupNrm[k * 3 + 2]);
      }
      revertedRoots.add(root);
      classByRoot.set(root, COMPONENT_CLASS.REVERTED_GUARD);
      tag.revertedComponents += 1;
      continue;
    }

    tag.repairedComponents += 1;
    repairedInfo.push({
      id: root,
      vertices: decomp.counts.get(root) ?? 0,
      preBox: {
        min: [preBox.min.x, preBox.min.y, preBox.min.z],
        max: [preBox.max.x, preBox.max.y, preBox.max.z],
      },
      postBox: {
        min: [postBox.min.x, postBox.min.y, postBox.min.z],
        max: [postBox.max.x, postBox.max.y, postBox.max.z],
      },
      pivotBaseY: baseY,
      scale: [1, COMPONENT_REPAIR_FACTOR, 1],
    });
  }

  tag.modifiedVertices = modified.reduce(
    (acc, vi) => acc + (repairSet.has(decomp.labels[vi]) && !revertedRoots.has(decomp.labels[vi]) ? 1 : 0),
    0,
  );

  pos.needsUpdate = true;
  if (nrm) nrm.needsUpdate = true;
  geo.computeBoundingBox();
  geo.computeBoundingSphere();

  const classes = new Uint8Array(pos.count);
  for (let i = 0; i < pos.count; i++) classes[i] = classByRoot.get(decomp.labels[i]) ?? COMPONENT_CLASS.UNCHANGED;
  repairStore.set(mesh, { classes, backupIndex, backupPos, backupNrm, repaired: repairedInfo });
  mesh.userData.odessaComponentRepair = tag;
  return tag;
}

/** Exact reversal of every modified vertex (positions + normals). */
export function revertComponentRepair(mesh: THREE.Mesh): boolean {
  const tag = mesh.userData.odessaComponentRepair as ComponentRepairTag | undefined;
  const data = repairStore.get(mesh);
  if (!tag || !data) return false;
  const pos = mesh.geometry?.getAttribute("position") as THREE.BufferAttribute | undefined;
  const nrm = mesh.geometry?.getAttribute("normal") as THREE.BufferAttribute | undefined;
  if (!pos) return false;
  for (let k = 0; k < data.backupIndex.length; k++) {
    const vi = data.backupIndex[k];
    pos.setXYZ(vi, data.backupPos[k * 3], data.backupPos[k * 3 + 1], data.backupPos[k * 3 + 2]);
    if (nrm && data.backupNrm) {
      nrm.setXYZ(vi, data.backupNrm[k * 3], data.backupNrm[k * 3 + 1], data.backupNrm[k * 3 + 2]);
    }
  }
  pos.needsUpdate = true;
  if (nrm) nrm.needsUpdate = true;
  mesh.geometry.computeBoundingBox();
  mesh.geometry.computeBoundingSphere();
  repairStore.delete(mesh);
  delete mesh.userData.odessaComponentRepair;
  return true;
}

/* ------------------------------------------------------------------ */
/* Scene-level driver + dev tooling support                             */
/* ------------------------------------------------------------------ */

export type SceneComponentRepairResult = {
  meshesRepaired: number;
  totalComponents: number;
  repairedComponents: number;
  miniatureComponents: number;
  uncertainComponents: number;
  revertedComponents: number;
  modifiedVertices: number;
};

export function emptySceneComponentRepairResult(): SceneComponentRepairResult {
  return {
    meshesRepaired: 0,
    totalComponents: 0,
    repairedComponents: 0,
    miniatureComponents: 0,
    uncertainComponents: 0,
    revertedComponents: 0,
    modifiedVertices: 0,
  };
}

/** Runs component repair on every mesh flagged `odessaMixedDomain` (the
 * generated "repair-components" verdict) under the given root. */
export function applySceneComponentRepair(root: THREE.Object3D): SceneComponentRepairResult {
  const result = emptySceneComponentRepairResult();
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh || !mesh.userData.odessaMixedDomain) return;
    const tag = repairBuildingComponents(mesh);
    if (!tag) return;
    result.meshesRepaired += 1;
    result.totalComponents += tag.totalComponents;
    result.repairedComponents += tag.repairedComponents;
    result.miniatureComponents += tag.miniatureComponents;
    result.uncertainComponents += tag.uncertainComponents;
    result.revertedComponents += tag.revertedComponents;
    result.modifiedVertices += tag.modifiedVertices;
  });
  return result;
}

/** Dev A/B: revert (original) or re-apply (repaired) across the city. */
export function setSceneComponentRepairEnabled(root: THREE.Object3D, enabled: boolean): number {
  let touched = 0;
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh || !mesh.userData.odessaMixedDomain) return;
    if (enabled) {
      if (!(mesh.userData.odessaComponentRepair as ComponentRepairTag | undefined)?.applied) {
        if (repairBuildingComponents(mesh)) touched += 1;
      }
    } else if (revertComponentRepair(mesh)) {
      touched += 1;
    }
  });
  return touched;
}

/** Component class at a picked face (ALT+click support). */
export function componentClassAtFace(mesh: THREE.Mesh, faceIndex: number): {
  cls: number;
  clsName: string;
  componentInfo: RepairedComponentInfo | null;
} | null {
  const data = repairStore.get(mesh);
  if (!data || faceIndex < 0) return null;
  const index = mesh.geometry.getIndex();
  const vi = index ? index.getX(faceIndex * 3) : faceIndex * 3;
  if (vi >= data.classes.length) return null;
  const cls = data.classes[vi];
  const names = ["UNCHANGED", "REPAIRED", "MINIATURE_SOURCE_ANOMALY", "FLAT", "UNCERTAIN", "REVERTED_GUARD"];
  let componentInfo: RepairedComponentInfo | null = null;
  if (cls === COMPONENT_CLASS.REPAIRED) {
    /* find which repaired component contains this vertex via backup index */
    const pos = mesh.geometry.getAttribute("position") as THREE.BufferAttribute;
    const p = new THREE.Vector3().fromBufferAttribute(pos, vi).applyMatrix4(mesh.matrixWorld);
    componentInfo =
      data.repaired.find(
        (r) =>
          p.x >= r.postBox.min[0] - 0.01 &&
          p.x <= r.postBox.max[0] + 0.01 &&
          p.z >= r.postBox.min[2] - 0.01 &&
          p.z <= r.postBox.max[2] + 0.01,
      ) ?? null;
  }
  return { cls, clsName: names[cls] ?? "UNKNOWN", componentInfo };
}

/**
 * Dev-only vertex-color overlay over the repaired meshes:
 * repaired=green, miniature anomalies=red, uncertain/guard-reverted=yellow,
 * flat/unchanged=gray. Original materials and any authored `color`
 * attribute are stashed and restored exactly on release.
 */
export class ComponentColorOverlay {
  private saved = new Map<
    THREE.Mesh,
    { material: THREE.Material | THREE.Material[]; colorAttr: THREE.BufferAttribute | null }
  >();
  private overlayMat = new THREE.MeshBasicMaterial({ vertexColors: true, name: "odessaComponentOverlay" });

  apply(root: THREE.Object3D, active: boolean) {
    if (!active) {
      this.restore();
      return;
    }
    root.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh || this.saved.has(mesh)) return;
      const data = repairStore.get(mesh);
      const pos = mesh.geometry?.getAttribute("position") as THREE.BufferAttribute | undefined;
      if (!data || !pos) return;
      const colors = new Float32Array(pos.count * 3);
      for (let i = 0; i < pos.count; i++) {
        const cls = data.classes[i];
        let r = 0.45, g = 0.45, b = 0.5; // unchanged/flat: gray
        if (cls === COMPONENT_CLASS.REPAIRED) {
          r = 0.1; g = 0.9; b = 0.25;
        } else if (cls === COMPONENT_CLASS.MINIATURE) {
          r = 1; g = 0.15; b = 0.15;
        } else if (cls === COMPONENT_CLASS.UNCERTAIN || cls === COMPONENT_CLASS.REVERTED_GUARD) {
          r = 1; g = 0.85; b = 0.1;
        }
        colors[i * 3] = r;
        colors[i * 3 + 1] = g;
        colors[i * 3 + 2] = b;
      }
      this.saved.set(mesh, {
        material: mesh.material,
        colorAttr: (mesh.geometry.getAttribute("color") as THREE.BufferAttribute | undefined) ?? null,
      });
      mesh.geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
      mesh.material = this.overlayMat;
    });
  }

  restore() {
    for (const [mesh, saved] of this.saved) {
      mesh.material = saved.material;
      if (saved.colorAttr) mesh.geometry.setAttribute("color", saved.colorAttr);
      else mesh.geometry.deleteAttribute("color");
    }
    this.saved.clear();
  }

  dispose() {
    this.restore();
    this.overlayMat.dispose();
  }
}
