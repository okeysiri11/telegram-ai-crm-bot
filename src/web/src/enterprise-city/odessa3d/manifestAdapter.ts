/**
 * Adapt Blender web manifest → internal OdessaManifest for streaming/loader.
 */

import {
  blenderBoundsToCity,
  layerForAssetType,
  tileCenterFromBounds,
  tileRadiusFromBounds,
  type BlenderManifestAsset,
  type BlenderWebManifest,
} from "./blenderManifest";
import { resolvePublicAssetUrl } from "./publicAssetUrl";
import type { OdessaManifest, OdessaManifestAsset, OdessaManifestTile } from "./types";

export function adaptBlenderManifest(raw: BlenderWebManifest): OdessaManifest {
  const geoTransform = {
    originLat: raw.geoTransform?.originLat ?? 46.4825,
    originLng: raw.geoTransform?.originLng ?? 30.7233,
    calibrated: raw.geoTransform?.calibrated ?? false,
  };

  const layers = raw.layers?.length
    ? raw.layers
    : [
        { id: "city", label: "Odessa city", defaultVisible: true },
        { id: "heavy", label: "Heavy buildings", defaultVisible: true },
      ];

  const tiles: OdessaManifestTile[] = raw.assets.map((asset) => assetToTile(asset));

  return {
    version: String(raw.version ?? "1"),
    cityId: "odessa",
    name: raw.name || "Odessa Digital Twin",
    center: { lat: geoTransform.originLat, lng: geoTransform.originLng, alt: 0 },
    geoTransform,
    cityBounds: raw.cityBounds,
    priorityTiles: raw.priorityAssets ?? [],
    layers,
    packageFormat: raw.packageFormat ?? "blender_web_v1",
    stats: raw.stats,
    tiles,
  };
}

function assetToTile(asset: BlenderManifestAsset): OdessaManifestTile {
  const bounds = asset.bounds ? blenderBoundsToCity(asset.bounds) : undefined;
  const centerScene = tileCenterFromBounds(bounds);
  const url = asset.url ? resolvePublicAssetUrl(asset.url) : resolvePublicAssetUrl(asset.path || "");
  const manifestAsset: OdessaManifestAsset = {
    id: asset.id,
    url,
    layer: asset.layer || layerForAssetType(asset.type),
    priority: asset.priority ?? priorityForType(asset.type),
    bounds,
    entityRef: asset.entityRef,
    label: asset.label || asset.id,
    sizeMb: asset.size_mb,
    sourceType: asset.type,
    triangles: asset.triangles,
    objects: asset.objects,
  };

  return {
    id: asset.id,
    label: asset.label || asset.id,
    center: { lat: 46.4825, lng: 30.7233 },
    centerScene,
    radiusM: tileRadiusFromBounds(bounds),
    assets: [manifestAsset],
  };
}

function priorityForType(type: string): number {
  switch (type) {
    case "top_level_tile":
      return 2;
    case "tile04_rest":
      return 4;
    case "heavy_mesh_chunk_step12":
      return 6;
    case "heavy_mesh_chunk_step13":
      return 7;
    default:
      return 5;
  }
}

/** Legacy STEP 15 scaffold manifest (tiles[] with nested assets). */
export function isLegacyOdessaManifest(json: unknown): json is OdessaManifest {
  return !!json && typeof json === "object" && Array.isArray((json as OdessaManifest).tiles) && !!(json as OdessaManifest).geoTransform;
}

export function isBlenderWebManifest(json: unknown): json is BlenderWebManifest {
  return !!json && typeof json === "object" && Array.isArray((json as BlenderWebManifest).assets);
}

export function parseOdessaManifestJson(json: unknown): OdessaManifest {
  if (isBlenderWebManifest(json)) return adaptBlenderManifest(json);
  if (isLegacyOdessaManifest(json)) return json;
  throw new Error("manifest_invalid:unknown_format");
}
