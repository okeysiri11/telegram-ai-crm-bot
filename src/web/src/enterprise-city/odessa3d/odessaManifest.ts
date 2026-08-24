/**
 * Fetch and validate odessa_manifest.json (Blender web or legacy STEP 15 format).
 */

import { ODESSA_MANIFEST_URL } from "./publicAssetUrl";
import { validateBlenderManifest, type BlenderWebManifest } from "./blenderManifest";
import { isBlenderWebManifest, parseOdessaManifestJson } from "./manifestAdapter";
import type { LoadingProgress, OdessaManifest } from "./types";

export async function loadOdessaManifest(url = ODESSA_MANIFEST_URL): Promise<OdessaManifest> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`manifest_fetch_failed:${res.status}`);
  const json = (await res.json()) as BlenderWebManifest;
  if (isBlenderWebManifest(json)) {
    const errors = validateBlenderManifest(json);
    if (errors.length) throw new Error(`manifest_invalid:${errors.join(",")}`);
  }
  const manifest = parseOdessaManifestJson(json);
  if (!manifest.tiles?.length) throw new Error("manifest_invalid:no_tiles");
  return manifest;
}

export function manifestAssetEntries(manifest: OdessaManifest) {
  const rows: {
    tileId: string;
    asset: OdessaManifest["tiles"][number]["assets"][number];
  }[] = [];
  for (const tile of manifest.tiles) {
    for (const asset of tile.assets) {
      rows.push({ tileId: tile.id, asset });
    }
  }
  return rows;
}

export function manifestProgress(
  total: number,
  loaded: number,
  failed: number,
  queued: number,
  loading: number,
  extras: Partial<LoadingProgress> = {},
): LoadingProgress {
  const done = loaded + failed;
  const percent = total ? Math.round((done / total) * 100) : 0;
  return { total, loaded, failed, queued, loading, percent, ...extras };
}
