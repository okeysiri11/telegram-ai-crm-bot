/**
 * Blender web export manifest types + validation helpers.
 */

import type { CityBounds, OdessaManifestLayer } from "./types";

export type BlenderManifestBounds = {
  min_x: number;
  max_x: number;
  min_y: number;
  max_y: number;
  min_z?: number;
  max_z?: number;
};

export type BlenderManifestAsset = {
  id: string;
  type: string;
  path?: string;
  url?: string;
  size_mb?: number;
  objects?: number;
  triangles?: number;
  bounds?: BlenderManifestBounds;
  layer?: string;
  entityRef?: string;
  label?: string;
  priority?: number;
  metadata?: Record<string, unknown>;
};

export type BlenderWebManifest = {
  name: string;
  version: number | string;
  packageFormat?: string;
  coordinate_system?: {
    height_axis: string;
    map_plane: string[];
  };
  loading_strategy?: string;
  notes?: string[];
  stats?: Record<string, number>;
  geoTransform?: {
    originLat: number;
    originLng: number;
    calibrated?: boolean;
  };
  cityBounds?: CityBounds;
  priorityAssets?: string[];
  layers?: OdessaManifestLayer[];
  assets: BlenderManifestAsset[];
};

const PUBLIC_ROOT = "/assets/odessa";

export function normalizeAssetUrl(pathOrUrl: string): string {
  const raw = pathOrUrl.trim().replace(/\\/g, "/");
  if (raw.startsWith("/assets/")) return raw;
  if (raw.startsWith("file://") || raw.includes("/Users/") || raw.includes("~/")) {
    throw new Error(`invalid_local_path:${raw}`);
  }
  const rel = raw.startsWith("/") ? raw.slice(1) : raw;
  return `${PUBLIC_ROOT}/${rel}`;
}

/** Blender export bounds → Three.js scene bounds (map Y → Z, height Z → Y). */
export function blenderBoundsToCity(bounds: BlenderManifestBounds): CityBounds {
  return {
    minX: bounds.min_x,
    maxX: bounds.max_x,
    minZ: bounds.min_y,
    maxZ: bounds.max_y,
    minY: bounds.min_z ?? 0,
    maxY: bounds.max_z ?? 0,
  };
}

export function layerForAssetType(type: string): string {
  if (type.startsWith("heavy_mesh")) return "heavy";
  return "city";
}

export function tileCenterFromBounds(bounds?: CityBounds): { x: number; z: number } | undefined {
  if (!bounds) return undefined;
  return {
    x: (bounds.minX + bounds.maxX) / 2,
    z: (bounds.minZ + bounds.maxZ) / 2,
  };
}

export function tileRadiusFromBounds(bounds?: CityBounds): number {
  if (!bounds) return 400;
  const w = bounds.maxX - bounds.minX;
  const d = bounds.maxZ - bounds.minZ;
  return Math.max(w, d) / 2 + 40;
}

export function validateBlenderManifest(json: BlenderWebManifest): string[] {
  const errors: string[] = [];
  if (!json?.assets?.length) errors.push("no_assets");
  const ids = new Set<string>();
  const urls = new Set<string>();
  for (const a of json.assets || []) {
    if (!a.id) errors.push("asset_missing_id");
    if (ids.has(a.id)) errors.push(`duplicate_id:${a.id}`);
    ids.add(a.id);
    const url = a.url || (a.path ? normalizeAssetUrl(a.path) : "");
    if (!url) errors.push(`asset_missing_url:${a.id}`);
    if (urls.has(url)) errors.push(`duplicate_url:${url}`);
    if (url) urls.add(url);
  }
  return errors;
}

export function manifestTotalMb(assets: BlenderManifestAsset[]): number {
  return assets.reduce((sum, a) => sum + (a.size_mb ?? 0), 0);
}
