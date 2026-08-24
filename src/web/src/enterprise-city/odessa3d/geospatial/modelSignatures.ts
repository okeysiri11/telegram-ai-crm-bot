/**
 * Model X/Z footprint signatures. AABB centers only — does not rename or move meshes.
 */

import type { LocalWorldCoordinate } from "./types";

export type ModelSignatureClass = "building" | "road" | "water" | "coast" | "other";

export type ModelXzSignature = {
  name: string;
  file: string;
  class: ModelSignatureClass;
  world: LocalWorldCoordinate;
  spanX: number;
  spanY: number;
  spanZ: number;
  cityWide: boolean;
};

export type ModelSignatureDocument = {
  package?: string;
  count?: number;
  buildings?: number;
  roads?: number;
  water?: number;
  rows: ModelXzSignature[];
};

/** Meshes larger than this in X or Z are city-wide batches, not individual features. */
export const CITYWIDE_SPAN_M = 2000;
/** Individual building AABBs used for footprint matching. */
export const LOCAL_BUILDING_MIN_SPAN_M = 8;
export const LOCAL_BUILDING_MAX_SPAN_M = 250;
export const LOCAL_ROAD_MAX_SPAN_M = 2000;

function isRecord(v: unknown): v is Record<string, unknown> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}

function isNum(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

export function classifyModelName(name: string): ModelSignatureClass {
  const n = name.toLowerCase();
  if (n.includes("coast") || n.includes("beach") || n.includes("natural_s")) return "coast";
  if (n.includes("water") || n.includes("river")) return "water";
  if (n.includes("highway") || n.includes("route_") || n.includes("railway")) return "road";
  if (n.includes("build") || n.includes("heavy_building")) return "building";
  return "other";
}

export function isCityWideSpan(spanX: number, spanZ: number, threshold = CITYWIDE_SPAN_M): boolean {
  return spanX > threshold || spanZ > threshold;
}

function rowFromUnknown(item: unknown): ModelXzSignature | null {
  if (!isRecord(item)) return null;
  const name = typeof item.name === "string" ? item.name : "";
  if (!name) return null;
  const spanX = isNum(item.spanX) ? item.spanX : isNum(item.dx) ? item.dx : null;
  const spanY = isNum(item.spanY) ? item.spanY : isNum(item.dy) ? item.dy : null;
  const spanZ = isNum(item.spanZ) ? item.spanZ : isNum(item.dz) ? item.dz : null;
  let x: number | null = isNum(item.cx) ? item.cx : null;
  let y: number | null = isNum(item.cy) ? item.cy : null;
  let z: number | null = isNum(item.cz) ? item.cz : null;
  if (isRecord(item.world) && isNum(item.world.x) && isNum(item.world.y) && isNum(item.world.z)) {
    x = item.world.x;
    y = item.world.y;
    z = item.world.z;
  }
  if (x == null || y == null || z == null || spanX == null || spanY == null || spanZ == null) return null;
  const clsRaw = item.class;
  const cls: ModelSignatureClass =
    clsRaw === "building" || clsRaw === "road" || clsRaw === "water" || clsRaw === "coast" || clsRaw === "other"
      ? clsRaw
      : classifyModelName(name);
  return {
    name,
    file: typeof item.file === "string" ? item.file : "",
    class: cls,
    world: { x, y, z },
    spanX,
    spanY,
    spanZ,
    cityWide: typeof item.cityWide === "boolean" ? item.cityWide : isCityWideSpan(spanX, spanZ),
  };
}

export function parseModelSignatures(raw: unknown): ModelSignatureDocument {
  const rowsIn = isRecord(raw) && Array.isArray(raw.rows) ? raw.rows : Array.isArray(raw) ? raw : [];
  const rows: ModelXzSignature[] = [];
  for (const item of rowsIn) {
    const row = rowFromUnknown(item);
    if (row) rows.push(row);
  }
  return {
    package: isRecord(raw) && typeof raw.package === "string" ? raw.package : undefined,
    count: rows.length,
    buildings: rows.filter((r) => r.class === "building").length,
    roads: rows.filter((r) => r.class === "road").length,
    water: rows.filter((r) => r.class === "water").length,
    rows,
  };
}

export function localBuildingSignatures(
  rows: readonly ModelXzSignature[],
  minSpan = LOCAL_BUILDING_MIN_SPAN_M,
  maxSpan = LOCAL_BUILDING_MAX_SPAN_M,
): ModelXzSignature[] {
  return rows.filter(
    (r) =>
      r.class === "building" &&
      !r.cityWide &&
      r.spanX >= minSpan &&
      r.spanZ >= minSpan &&
      r.spanX <= maxSpan &&
      r.spanZ <= maxSpan,
  );
}

export function localRoadSignatures(rows: readonly ModelXzSignature[], maxSpan = LOCAL_ROAD_MAX_SPAN_M): ModelXzSignature[] {
  return rows.filter((r) => r.class === "road" && !r.cityWide && r.spanX <= maxSpan && r.spanZ <= maxSpan);
}

export function waterSignatures(rows: readonly ModelXzSignature[]): ModelXzSignature[] {
  return rows.filter((r) => r.class === "water" || r.class === "coast");
}
