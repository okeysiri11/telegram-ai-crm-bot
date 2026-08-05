/**
 * City Engine (presentation) — Sprint 27.8.
 * Camera · zoom · pan · viewport memory. Not a business runtime.
 * Reuses session keys; no duplicated platform stores.
 */

import type { CityBuilding } from "./cityCatalog";

export const CITY_VIEWPORT_KEY = "ews_city_viewport_v1";
export const CITY_EXPERIENCE_CORE = "27.8";

export type CityViewport = {
  x: number;
  y: number;
  zoom: number;
};

export const DEFAULT_VIEWPORT: CityViewport = { x: 0, y: 0, zoom: 1 };

const ZOOM_MIN = 0.65;
const ZOOM_MAX = 1.75;
const PAN_LIMIT = 35;

export function clampZoom(z: number): number {
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, z));
}

export function clampPan(n: number): number {
  return Math.min(PAN_LIMIT, Math.max(-PAN_LIMIT, n));
}

export function clampViewport(v: CityViewport): CityViewport {
  return { x: clampPan(v.x), y: clampPan(v.y), zoom: clampZoom(v.zoom) };
}

/** Center camera on a building (percent space). */
export function panToBuilding(b: CityBuilding, current?: CityViewport): CityViewport {
  return clampViewport({
    x: 50 - (b.x + b.w / 2),
    y: 50 - (b.y + b.h / 2),
    zoom: current?.zoom ?? 1.15,
  });
}

export function zoomBy(v: CityViewport, delta: number): CityViewport {
  return clampViewport({ ...v, zoom: v.zoom + delta });
}

export function applyPanDelta(v: CityViewport, dxPct: number, dyPct: number): CityViewport {
  return clampViewport({ ...v, x: v.x + dxPct, y: v.y + dyPct });
}

export function readViewport(): CityViewport {
  try {
    const raw = sessionStorage.getItem(CITY_VIEWPORT_KEY);
    if (!raw) return { ...DEFAULT_VIEWPORT };
    const parsed = JSON.parse(raw) as CityViewport;
    return clampViewport({
      x: Number(parsed.x) || 0,
      y: Number(parsed.y) || 0,
      zoom: Number(parsed.zoom) || 1,
    });
  } catch {
    return { ...DEFAULT_VIEWPORT };
  }
}

export function writeViewport(v: CityViewport) {
  try {
    sessionStorage.setItem(CITY_VIEWPORT_KEY, JSON.stringify(clampViewport(v)));
  } catch {
    /* ignore */
  }
}

/** Minimap viewport rectangle (approximate visible window in % space). */
export function viewportRect(v: CityViewport): { left: number; top: number; width: number; height: number } {
  const width = 100 / v.zoom;
  const height = 100 / v.zoom;
  const left = 50 - width / 2 - v.x;
  const top = 50 - height / 2 - v.y;
  return { left, top, width, height };
}
