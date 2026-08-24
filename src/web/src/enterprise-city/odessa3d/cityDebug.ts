/**
 * Temporary developer overlay — enabled only with ?cityDebug=1
 */

export function isCityDebugEnabled(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return new URLSearchParams(window.location.search).get("cityDebug") === "1";
  } catch {
    return false;
  }
}

export type CityGeoDebug = {
  status: string;
  controlPoints: number;
  yaw: number | null;
  scale: number | null;
  axis: string;
  meanError: number | null;
  maxError: number | null;
  cameraLat: number | null;
  cameraLon: number | null;
  cameraAlt: number | null;
  cameraEnu: { east: number; north: number; up: number } | null;
  selectedLat: number | null;
  selectedLon: number | null;
};

export type CityDebugSnapshot = {
  fps: number;
  camera: { x: number; y: number; z: number };
  target: { x: number; y: number; z: number };
  hovered: string | null;
  selected: string | null;
  hoveredCoords: { x: number; y: number; z: number } | null;
  selectedCoords: { x: number; y: number; z: number } | null;
  viewMode: "2d" | "3d";
  geo?: CityGeoDebug;
};

export function emptyCityDebugSnapshot(): CityDebugSnapshot {
  return {
    fps: 0,
    camera: { x: 0, y: 0, z: 0 },
    target: { x: 0, y: 0, z: 0 },
    hovered: null,
    selected: null,
    hoveredCoords: null,
    selectedCoords: null,
    viewMode: "3d",
    geo: undefined,
  };
}

export function formatCityGeoDebug(snap: CityDebugSnapshot): string {
  const g = snap.geo;
  return [
    "GEOREFERENCE",
    `Status: ${g?.status ?? "—"}`,
    `Control points: ${g?.controlPoints ?? 0}`,
    `Yaw: ${g?.yaw ?? "—"}`,
    `Scale: ${g?.scale ?? "—"}`,
    `Axis: ${g?.axis ?? "—"}`,
    `Mean error: ${g?.meanError ?? "—"}`,
    `Max error: ${g?.maxError ?? "—"}`,
    `Camera lat/lon: ${g?.cameraLat ?? "—"}, ${g?.cameraLon ?? "—"}`,
    `Selected lat/lon: ${g?.selectedLat ?? "—"}, ${g?.selectedLon ?? "—"}`,
    `Camera world: ${snap.camera.x.toFixed(2)} ${snap.camera.y.toFixed(2)} ${snap.camera.z.toFixed(2)}`,
  ].join("\n");
}
