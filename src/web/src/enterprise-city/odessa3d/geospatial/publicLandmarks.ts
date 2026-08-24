/**
 * Public landmark catalog parser/cache. Does not invent model correspondences.
 */

import type { GeoCoordinate } from "./types";

export type PublicLandmark = {
  id: string;
  name: string;
  aliases: string[];
  gps: GeoCoordinate;
  source: string;
};

export type PublicLandmarkCache = {
  schemaVersion: 1;
  region: string;
  landmarks: PublicLandmark[];
};

/** Cited public WGS84 only — never used as controls unless a model name matches exactly. */
export const CITED_ODESSA_PUBLIC_LANDMARKS: readonly PublicLandmark[] = [
  {
    id: "wikidata-Q195513",
    name: "Odesa Opera and Ballet Theatre",
    aliases: ["odessa opera", "odesa opera", "opera house"],
    gps: { lat: 46.485556, lon: 30.741667 },
    source: "Wikipedia / Wikidata Q195513",
  },
];

export function normalizeLandmarkName(raw: string): string {
  return raw
    .toLowerCase()
    .replace(/^web_name_+/i, "")
    .replace(/[_]+/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

export function parsePublicLandmarkCache(raw: unknown): PublicLandmarkCache {
  if (!raw || typeof raw !== "object") return { schemaVersion: 1, region: "unknown", landmarks: [] };
  const rec = raw as Record<string, unknown>;
  const landmarks: PublicLandmark[] = [];
  const list = Array.isArray(rec.landmarks) ? rec.landmarks : Array.isArray(rec.features) ? rec.features : [];
  for (const item of list) {
    const parsed = parseOneLandmark(item);
    if (parsed) landmarks.push(parsed);
  }
  return {
    schemaVersion: 1,
    region: typeof rec.region === "string" ? rec.region : "unknown",
    landmarks,
  };
}

function parseOneLandmark(item: unknown): PublicLandmark | null {
  if (!item || typeof item !== "object") return null;
  const rec = item as Record<string, unknown>;
  if (rec.type === "Feature" && rec.geometry && rec.properties) {
    const geom = rec.geometry as { type?: string; coordinates?: unknown };
    const props = rec.properties as Record<string, unknown>;
    if (geom.type !== "Point" || !Array.isArray(geom.coordinates) || geom.coordinates.length < 2) return null;
    const lon = Number(geom.coordinates[0]);
    const lat = Number(geom.coordinates[1]);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    const name = String(props.name ?? props.label ?? "");
    if (!name) return null;
    return {
      id: String(props.id ?? props.osm_id ?? name),
      name,
      aliases: Array.isArray(props.aliases) ? props.aliases.map(String) : [],
      gps: { lat, lon },
      source: String(props.source ?? "geojson"),
    };
  }
  const name = typeof rec.name === "string" ? rec.name : "";
  const gps = rec.gps && typeof rec.gps === "object" ? (rec.gps as Record<string, unknown>) : rec;
  const lat = Number(gps.lat);
  const lon = Number(gps.lon ?? gps.lng);
  if (!name || !Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  return {
    id: String(rec.id ?? name),
    name,
    aliases: Array.isArray(rec.aliases) ? rec.aliases.map(String) : [],
    gps: { lat, lon },
    source: String(rec.source ?? "object"),
  };
}

export function loadPublicLandmarkCache(raw?: unknown): PublicLandmark[] {
  const parsed = parsePublicLandmarkCache(raw ?? { landmarks: CITED_ODESSA_PUBLIC_LANDMARKS, region: "odesa" });
  const seen = new Set<string>();
  const out: PublicLandmark[] = [];
  for (const lm of [...CITED_ODESSA_PUBLIC_LANDMARKS, ...parsed.landmarks]) {
    if (seen.has(lm.id)) continue;
    seen.add(lm.id);
    out.push(lm);
  }
  return out;
}
