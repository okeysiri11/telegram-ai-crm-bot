/**
 * Runtime water classification, duplicate guard, and stable materials.
 * Does not delete Blender/GLB geometry — hides true duplicate sea surfaces only.
 */

import * as THREE from "three";
import { activeOdessaPackage } from "./odessaPackage";

export type WaterCategory = "sea" | "river" | "lake" | "canal" | "port" | "generic";

export type WaterSurfaceRecord = {
  mesh: THREE.Mesh;
  name: string;
  category: WaterCategory;
  minY: number;
  maxY: number;
  midY: number;
  areaXZ: number;
  bounds: { min: { x: number; y: number; z: number }; max: { x: number; y: number; z: number } };
  materialType: string;
  transparent: boolean;
  depthWrite: boolean;
  depthTest: boolean;
  side: number;
  renderOrder: number;
  metalness: number;
  roughness: number;
  hiddenAsDuplicate: boolean;
  duplicateOf: string | null;
};

export type WaterGuardResult = {
  meshCount: number;
  kept: number;
  duplicatesHidden: number;
  records: WaterSurfaceRecord[];
};

export type WaterGuardOptions = {
  debug?: boolean;
};

const STRUCTURE_EXCLUDE = /water[_\s-]?tower|wastewater|water[_\s-]?well|breakwater|fountain/;
const WATER_TOKEN = /(^|[_\s.-])(water|sea|ocean|lake|river|rivers|pond|bay|canal|harbor|harbour|lagoon)(s)?($|[_\s.-])/i;
const PROTECTED: ReadonlySet<WaterCategory> = new Set(["river", "lake", "canal", "port"]);

const SEA_CONTAINMENT = 0.85;
const SEA_IOU = 0.32;
/* STEP 29.9: authored in the legacy 1/100 frame; scaled by the active
 * package so the metric city (layer offsets ×100) keeps the same behavior. */
const yProximity = () => 0.15 * activeOdessaPackage().decalYScale;
const thinY = () => 2.5 * activeOdessaPackage().decalYScale;

const DEBUG_COLORS: Record<WaterCategory | "duplicate", number> = {
  sea: 0x00c8ff,
  river: 0x39ff14,
  lake: 0xffee00,
  canal: 0x00ffaa,
  port: 0xff8800,
  generic: 0xffffff,
  duplicate: 0xff00aa,
};

const STABLE_ROUGHNESS = 0.68;
const STABLE_METALNESS = 0;

type WaterUserData = {
  stabilized?: boolean;
  originalVisible?: boolean;
  originalColor?: number;
  originalRoughness?: number;
  originalMetalness?: number;
  debugCloned?: boolean;
  hiddenAsDuplicate?: boolean;
};

function waterData(mesh: THREE.Mesh): WaterUserData {
  const ud = mesh.userData as { odessaWater?: WaterUserData };
  if (!ud.odessaWater) ud.odessaWater = {};
  return ud.odessaWater;
}

export function nameLooksLikeWater(name: string): boolean {
  const n = (name || "").trim();
  if (!n) return false;
  const lower = n.toLowerCase();
  if (STRUCTURE_EXCLUDE.test(lower)) return false;
  if (lower === "water") return true;
  return WATER_TOKEN.test(lower);
}

export function waterCategoryFromName(name: string): WaterCategory {
  const n = (name || "").toLowerCase();
  if (/river|stream/.test(n)) return "river";
  if (/lake|pond/.test(n)) return "lake";
  if (/canal/.test(n)) return "canal";
  if (/port|harbor|harbour|basin/.test(n)) return "port";
  if (/sea|ocean|bay/.test(n) || /(^|[_\s.-])water($|[_\s.-])/.test(n) || n === "water") return "sea";
  return "generic";
}

export function isWaterLikeMesh(mesh: THREE.Mesh): boolean {
  if (!mesh.isMesh) return false;
  if (nameLooksLikeWater(mesh.name) || nameLooksLikeWater(mesh.parent?.name || "")) return true;
  const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  return materials.some((m) => m && nameLooksLikeWater(m.name || ""));
}

function materialsOf(mesh: THREE.Mesh): THREE.Material[] {
  return (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).filter(Boolean);
}

function aabbAreaXZ(box: THREE.Box3): number {
  const dx = Math.max(0, box.max.x - box.min.x);
  const dz = Math.max(0, box.max.z - box.min.z);
  return dx * dz;
}

function overlapAreaXZ(a: THREE.Box3, b: THREE.Box3): number {
  const ix = Math.max(0, Math.min(a.max.x, b.max.x) - Math.max(a.min.x, b.min.x));
  const iz = Math.max(0, Math.min(a.max.z, b.max.z) - Math.max(a.min.z, b.min.z));
  return ix * iz;
}

function iouXZ(a: THREE.Box3, b: THREE.Box3): number {
  const inter = overlapAreaXZ(a, b);
  const union = aabbAreaXZ(a) + aabbAreaXZ(b) - inter;
  return union > 0 ? inter / union : 0;
}

function containmentXZ(inner: THREE.Box3, outer: THREE.Box3): number {
  const area = aabbAreaXZ(inner);
  return area > 0 ? overlapAreaXZ(inner, outer) / area : 0;
}

function keepScore(name: string, area: number, verts: number): number {
  const n = name.toLowerCase();
  let score = area + verts * 0.01;
  if (n === "web_water" || n.endsWith("_water") || n === "water") score += 1e9;
  if (/\bsea\b|ocean/.test(n)) score += 5e8;
  return score;
}

function vertexCount(mesh: THREE.Mesh): number {
  const pos = mesh.geometry?.attributes.position;
  return pos ? pos.count : 0;
}

export function stabilizeWaterMaterial(mat: THREE.Material) {
  const std = mat as THREE.MeshStandardMaterial;
  if (!std.isMeshStandardMaterial && !(mat as THREE.MeshPhongMaterial).isMeshPhongMaterial) {
    mat.side = THREE.FrontSide;
    mat.depthWrite = true;
    mat.depthTest = true;
    mat.transparent = false;
    mat.needsUpdate = true;
    return;
  }
  std.metalness = STABLE_METALNESS;
  std.roughness = Math.max(std.roughness ?? 0, STABLE_ROUGHNESS);
  std.envMap = null;
  std.envMapIntensity = 0;
  std.transparent = false;
  std.opacity = 1;
  std.depthWrite = true;
  std.depthTest = true;
  std.side = THREE.FrontSide;
  if ("emissive" in std && std.emissive) std.emissive.setHex(0x000000);
  std.needsUpdate = true;
}

function applyPolygonOffset(mat: THREE.Material) {
  mat.polygonOffset = true;
  mat.polygonOffsetFactor = 1;
  mat.polygonOffsetUnits = 1;
  mat.needsUpdate = true;
}

function toRecord(mesh: THREE.Mesh, box: THREE.Box3, hidden: boolean, duplicateOf: string | null): WaterSurfaceRecord {
  const mats = materialsOf(mesh);
  const mat = mats[0] as THREE.MeshStandardMaterial | undefined;
  const parentName = mesh.parent?.name || "";
  const label = nameLooksLikeWater(mesh.name) ? mesh.name : parentName || mesh.name || mat?.name || "water";
  return {
    mesh,
    name: label,
    category: waterCategoryFromName(`${label} ${mat?.name || ""}`),
    minY: box.min.y,
    maxY: box.max.y,
    midY: (box.min.y + box.max.y) * 0.5,
    areaXZ: aabbAreaXZ(box),
    bounds: {
      min: { x: box.min.x, y: box.min.y, z: box.min.z },
      max: { x: box.max.x, y: box.max.y, z: box.max.z },
    },
    materialType: mat?.type || "Material",
    transparent: !!mat?.transparent,
    depthWrite: mat?.depthWrite !== false,
    depthTest: mat?.depthTest !== false,
    side: mat?.side ?? THREE.FrontSide,
    renderOrder: mesh.renderOrder,
    metalness: mat?.metalness ?? 0,
    roughness: mat?.roughness ?? 1,
    hiddenAsDuplicate: hidden,
    duplicateOf,
  };
}

export function collectWaterMeshes(roots: Iterable<THREE.Object3D>): THREE.Mesh[] {
  const out: THREE.Mesh[] = [];
  for (const root of roots) {
    root.updateMatrixWorld(true);
    root.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (mesh.isMesh && isWaterLikeMesh(mesh)) out.push(mesh);
    });
  }
  return out;
}

function isSeaLike(category: WaterCategory): boolean {
  return category === "sea" || category === "generic";
}

/**
 * Identify equivalent overlapping sea surfaces. Rivers/lakes/canals/ports stay visible
 * even when their AABB overlaps the sea.
 */
export function findDuplicateWaterMeshes(
  meshes: THREE.Mesh[],
): Map<THREE.Mesh, { hide: boolean; duplicateOf: string | null }> {
  const boxes = new Map<THREE.Mesh, THREE.Box3>();
  const meta = meshes.map((mesh) => {
    const box = new THREE.Box3().setFromObject(mesh);
    boxes.set(mesh, box);
    const label = `${mesh.name} ${mesh.parent?.name || ""} ${materialsOf(mesh)[0]?.name || ""}`;
    return {
      mesh,
      box,
      category: waterCategoryFromName(label),
      area: aabbAreaXZ(box),
      yExtent: box.max.y - box.min.y,
      midY: (box.min.y + box.max.y) * 0.5,
      score: keepScore(mesh.parent?.name || mesh.name, aabbAreaXZ(box), vertexCount(mesh)),
    };
  });

  const decision = new Map<THREE.Mesh, { hide: boolean; duplicateOf: string | null }>();
  for (const m of meshes) decision.set(m, { hide: false, duplicateOf: null });

  const sea = meta.filter((m) => isSeaLike(m.category) && m.yExtent < thinY());
  sea.sort((a, b) => b.score - a.score);

  for (let i = 0; i < sea.length; i++) {
    const keep = sea[i];
    if (decision.get(keep.mesh)?.hide) continue;
    for (let j = i + 1; j < sea.length; j++) {
      const other = sea[j];
      if (decision.get(other.mesh)?.hide) continue;
      if (Math.abs(keep.midY - other.midY) > yProximity()) continue;
      const smaller = other.area <= keep.area ? other : keep;
      const larger = smaller === other ? keep : other;
      const contained = containmentXZ(smaller.box, larger.box);
      const iou = iouXZ(keep.box, other.box);
      if (contained < SEA_CONTAINMENT && iou < SEA_IOU) continue;
      const loser = keep.score >= other.score ? other : keep;
      const winner = loser === other ? keep : other;
      decision.set(loser.mesh, { hide: true, duplicateOf: winner.mesh.parent?.name || winner.mesh.name });
    }
  }
  return decision;
}

function applyDebugAppearance(mesh: THREE.Mesh, category: WaterCategory, duplicate: boolean, on: boolean) {
  const data = waterData(mesh);
  const mats = materialsOf(mesh);
  for (const mat of mats) {
    const std = mat as THREE.MeshStandardMaterial;
    if (!std.color) continue;
    if (data.originalColor == null) data.originalColor = std.color.getHex();
    if (on) {
      std.color.setHex(duplicate ? DEBUG_COLORS.duplicate : DEBUG_COLORS[category]);
    } else if (data.originalColor != null) {
      std.color.setHex(data.originalColor);
    }
    std.needsUpdate = true;
  }
}

export function applyWaterSurfaceGuard(roots: Iterable<THREE.Object3D>, opts: WaterGuardOptions = {}): WaterGuardResult {
  const debug = opts.debug ?? false;
  const meshes = collectWaterMeshes(roots);
  const duplicates = findDuplicateWaterMeshes(meshes);
  const records: WaterSurfaceRecord[] = [];
  let hiddenCount = 0;

  const boxes = new Map<THREE.Mesh, THREE.Box3>();
  for (const mesh of meshes) {
    boxes.set(mesh, new THREE.Box3().setFromObject(mesh));
  }

  const visibleSea: { mesh: THREE.Mesh; box: THREE.Box3 }[] = [];

  for (const mesh of meshes) {
    const data = waterData(mesh);
    if (data.originalVisible == null) data.originalVisible = mesh.visible;

    for (const mat of materialsOf(mesh)) {
      if (!data.stabilized) {
        const std = mat as THREE.MeshStandardMaterial;
        if (data.originalRoughness == null && std.roughness != null) data.originalRoughness = std.roughness;
        if (data.originalMetalness == null && std.metalness != null) data.originalMetalness = std.metalness;
        stabilizeWaterMaterial(mat);
      }
    }
    data.stabilized = true;

    const dup = duplicates.get(mesh) || { hide: false, duplicateOf: null };
    data.hiddenAsDuplicate = dup.hide;
    if (dup.hide) hiddenCount += 1;
    mesh.visible = debug ? true : !dup.hide;

    const box = boxes.get(mesh)!;
    const rec = toRecord(mesh, box, dup.hide, dup.duplicateOf);
    applyDebugAppearance(mesh, rec.category, dup.hide, debug);
    records.push(rec);

    if (!dup.hide) {
      if (isSeaLike(rec.category)) visibleSea.push({ mesh, box });
    }
  }

  for (const mesh of meshes) {
    const rec = records.find((r) => r.mesh === mesh);
    if (!rec || rec.hiddenAsDuplicate) continue;
    if (!PROTECTED.has(rec.category)) continue;
    const box = boxes.get(mesh)!;
    const coplanarSea = visibleSea.some(
      (s) => Math.abs(rec.midY - (s.box.min.y + s.box.max.y) * 0.5) < yProximity() && overlapAreaXZ(box, s.box) > 0,
    );
    if (coplanarSea) {
      for (const mat of materialsOf(mesh)) applyPolygonOffset(mat);
      mesh.renderOrder = 1;
    }
  }

  return {
    meshCount: meshes.length,
    kept: meshes.length - hiddenCount,
    duplicatesHidden: hiddenCount,
    records,
  };
}
