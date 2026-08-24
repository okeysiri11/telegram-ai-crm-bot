/**
 * Interactive-pick whitelist. Sea, ground, roads, and city-scale merged
 * batches must never enter the hover/selection raycast set.
 *
 * Does not mutate geometry or materials.
 */

import * as THREE from "three";
import { isWaterLikeMesh } from "../waterSurfaceGuard";

/** Mesh names that are background / OSM / water / labels — never pickable. */
export const EXCLUDED_PICK_NAME_RE =
  /(^|_)(base|plane|rivers?|roads?|highway|landuse|leisure|natural|amenity|railway|aeroway|barrier|boundary|waterway|power|labels?|name$|man_stroke|others|Roads|port|harbor|harbour|pier|dock|quay|terrain|ground|sea|ocean|veg|tree|grass|park|coast)(_|$|\d)/i;

export const BUILDING_PICK_NAME_RE = /build|height_|house|roof|facade|façade|tower|apart|office|bldg/i;

const NON_INTERACTIVE_CLASS = new Set(["WATER", "ROAD", "GROUND", "VEGETATION"]);
const INTERACTIVE_CLASS = new Set(["BUILDING", "INDUSTRIAL"]);

/** Merged district chunks (tens of km) are not a single selectable object. */
export const MAX_INTERACTIVE_FOOTPRINT_M = 400;
export const MIN_INTERACTIVE_HEIGHT_M = 2;

export type PickFilterReason =
  | "ok"
  | "no-mesh"
  | "water"
  | "excluded-name"
  | "non-interactive-class"
  | "too-flat"
  | "city-scale-merge";

export function classificationOfMesh(mesh: THREE.Mesh): string | undefined {
  const fromMesh = mesh.userData?.odessaMaterialClass;
  if (typeof fromMesh === "string") return fromMesh;
  const mat = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
  const fromMat = mat?.userData?.odessaMaterialClass;
  return typeof fromMat === "string" ? fromMat : undefined;
}

function worldBox(mesh: THREE.Mesh): THREE.Box3 | null {
  if (!mesh.geometry) return null;
  mesh.updateWorldMatrix(true, false);
  const box = new THREE.Box3().setFromObject(mesh);
  return box.isEmpty() ? null : box;
}

/**
 * True only for compact, building-like meshes. Used at register time so
 * hover/click never see the sea, terrain, or a 40 km merged chunk.
 */
export function isInteractivePickMesh(mesh: THREE.Mesh): { ok: boolean; reason: PickFilterReason } {
  if (!mesh.isMesh || !mesh.geometry) return { ok: false, reason: "no-mesh" };
  if (mesh.userData?.odessaHighlightHelper) return { ok: false, reason: "no-mesh" };
  if (isWaterLikeMesh(mesh)) return { ok: false, reason: "water" };

  const name = mesh.name || "";
  if (EXCLUDED_PICK_NAME_RE.test(name)) return { ok: false, reason: "excluded-name" };

  const cls = classificationOfMesh(mesh);
  if (cls && NON_INTERACTIVE_CLASS.has(cls)) return { ok: false, reason: "non-interactive-class" };

  const box = worldBox(mesh);
  if (!box) return { ok: false, reason: "no-mesh" };
  const h = box.max.y - box.min.y;
  const foot = Math.max(box.max.x - box.min.x, box.max.z - box.min.z);
  if (foot > MAX_INTERACTIVE_FOOTPRINT_M) return { ok: false, reason: "city-scale-merge" };
  if (h < MIN_INTERACTIVE_HEIGHT_M) return { ok: false, reason: "too-flat" };

  if (cls && INTERACTIVE_CLASS.has(cls)) return { ok: true, reason: "ok" };
  if (BUILDING_PICK_NAME_RE.test(name)) return { ok: true, reason: "ok" };
  /* unnamed compact extrusion — treat as a building candidate */
  if (h >= MIN_INTERACTIVE_HEIGHT_M && foot >= 2 && foot <= MAX_INTERACTIVE_FOOTPRINT_M) {
    return { ok: true, reason: "ok" };
  }
  return { ok: false, reason: "too-flat" };
}
