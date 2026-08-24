/**
 * 2D-assisted GPS for Odessa calibration.
 *
 * Enterprise City 2D uses a 0–100 plane (`planeToGeo`). That is not WGS84.
 * Do not read lat/lon from city-plane clicks.
 *
 * Sequential workflow: 3D pick → open Odessa OSM helper → paste real GPS.
 * Split 3D+2D layout is not used — it would rewrite the city shell.
 */

import { odessaMapHelperUrl, parseLatLonPair } from "./gpsValidation";

export const CITY_2D_MAP_IS_GEOGRAPHIC = false;

export type MapAssistedPickWorkflow = "osm-helper-paste";

export function mapAssistedPickWorkflow(): MapAssistedPickWorkflow {
  return "osm-helper-paste";
}

export function mapHelperOpenUrl(): string {
  return odessaMapHelperUrl();
}

/** Apply a pasted "lat, lon" or "lat lon" pair after the user copies GPS from the helper map. */
export function applyMapAssistedPaste(raw: string): { latText: string; lonText: string } | null {
  return parseLatLonPair(raw);
}
