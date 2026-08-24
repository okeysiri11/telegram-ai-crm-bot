/**
 * Overpass OSM geometry parser. Read-only — does not invent GPS identities.
 */

import type { GeoCoordinate } from "./types";
import { ODESSA_ENU_ORIGIN, wgs84ToLocalMeters } from "./localMeters";

export type OsmBounds = {
  minlat: number;
  minlon: number;
  maxlat: number;
  maxlon: number;
};

export type OsmLatLon = { lat: number; lon: number };

export type OsmElement = {
  type: string;
  id: number;
  lat?: number;
  lon?: number;
  center?: OsmLatLon;
  bounds?: OsmBounds;
  geometry?: OsmLatLon[];
  tags?: Record<string, string>;
};

export type OsmDocument = {
  elements: OsmElement[];
};

export type OsmBuildingFootprint = {
  id: number;
  geo: GeoCoordinate;
  spanEastM: number;
  spanNorthM: number;
  tags: Record<string, string>;
};

export type OsmPolyline = {
  id: number;
  kind: "road" | "coastline";
  points: GeoCoordinate[];
  lengthM: number;
  spanEastM: number;
  spanNorthM: number;
  tags: Record<string, string>;
};

function isRecord(v: unknown): v is Record<string, unknown> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}

function isNum(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

function parseLatLon(v: unknown): OsmLatLon | null {
  if (!isRecord(v) || !isNum(v.lat) || !isNum(v.lon)) return null;
  if (Math.abs(v.lat) > 90 || Math.abs(v.lon) > 180) return null;
  return { lat: v.lat, lon: v.lon };
}

function parseBounds(v: unknown): OsmBounds | null {
  if (!isRecord(v)) return null;
  if (!isNum(v.minlat) || !isNum(v.maxlat) || !isNum(v.minlon) || !isNum(v.maxlon)) return null;
  return { minlat: v.minlat, maxlat: v.maxlat, minlon: v.minlon, maxlon: v.maxlon };
}

function parseTags(v: unknown): Record<string, string> {
  if (!isRecord(v)) return {};
  const out: Record<string, string> = {};
  for (const [k, val] of Object.entries(v)) {
    if (typeof val === "string") out[k] = val;
  }
  return out;
}

export function parseOsmDocument(raw: unknown): OsmDocument {
  if (!isRecord(raw) || !Array.isArray(raw.elements)) return { elements: [] };
  const elements: OsmElement[] = [];
  for (const item of raw.elements) {
    if (!isRecord(item) || typeof item.type !== "string" || !isNum(item.id)) continue;
    const el: OsmElement = { type: item.type, id: item.id };
    if (isNum(item.lat) && isNum(item.lon)) {
      el.lat = item.lat;
      el.lon = item.lon;
    }
    const center = parseLatLon(item.center);
    if (center) el.center = center;
    const bounds = parseBounds(item.bounds);
    if (bounds) el.bounds = bounds;
    if (Array.isArray(item.geometry)) {
      const geom: OsmLatLon[] = [];
      for (const g of item.geometry) {
        const p = parseLatLon(g);
        if (p) geom.push(p);
      }
      if (geom.length) el.geometry = geom;
    }
    el.tags = parseTags(item.tags);
    elements.push(el);
  }
  return { elements };
}

export function boundsFromGeometry(geometry: readonly OsmLatLon[]): OsmBounds | null {
  if (!geometry.length) return null;
  let minlat = Infinity;
  let maxlat = -Infinity;
  let minlon = Infinity;
  let maxlon = -Infinity;
  for (const p of geometry) {
    minlat = Math.min(minlat, p.lat);
    maxlat = Math.max(maxlat, p.lat);
    minlon = Math.min(minlon, p.lon);
    maxlon = Math.max(maxlon, p.lon);
  }
  if (!Number.isFinite(minlat)) return null;
  return { minlat, maxlat, minlon, maxlon };
}

export function footprintSpansM(bounds: OsmBounds, origin = ODESSA_ENU_ORIGIN): { spanEastM: number; spanNorthM: number } {
  const sw = wgs84ToLocalMeters({ lat: bounds.minlat, lon: bounds.minlon }, origin);
  const ne = wgs84ToLocalMeters({ lat: bounds.maxlat, lon: bounds.maxlon }, origin);
  return {
    spanEastM: Math.abs(ne.east - sw.east),
    spanNorthM: Math.abs(ne.north - sw.north),
  };
}

export function boundsCenter(bounds: OsmBounds): GeoCoordinate {
  return {
    lat: (bounds.minlat + bounds.maxlat) / 2,
    lon: (bounds.minlon + bounds.maxlon) / 2,
  };
}

function polylineLengthM(points: readonly GeoCoordinate[], origin = ODESSA_ENU_ORIGIN): number {
  let len = 0;
  for (let i = 1; i < points.length; i++) {
    const a = wgs84ToLocalMeters(points[i - 1], origin);
    const b = wgs84ToLocalMeters(points[i], origin);
    len += Math.hypot(a.east - b.east, a.north - b.north);
  }
  return len;
}

function elementBounds(el: OsmElement): OsmBounds | null {
  if (el.bounds) return el.bounds;
  if (el.geometry) return boundsFromGeometry(el.geometry);
  return null;
}

function elementCenter(el: OsmElement, bounds: OsmBounds | null): GeoCoordinate | null {
  if (el.center) return { lat: el.center.lat, lon: el.center.lon };
  if (isNum(el.lat) && isNum(el.lon)) return { lat: el.lat, lon: el.lon };
  if (bounds) return boundsCenter(bounds);
  return null;
}

export function extractOsmBuildings(doc: OsmDocument, origin = ODESSA_ENU_ORIGIN): OsmBuildingFootprint[] {
  const out: OsmBuildingFootprint[] = [];
  for (const el of doc.elements) {
    const tags = el.tags ?? {};
    if (!tags.building && el.type !== "way") continue;
    if (!tags.building) continue;
    const bounds = elementBounds(el);
    const geo = elementCenter(el, bounds);
    if (!geo) continue;
    const spans = bounds ? footprintSpansM(bounds, origin) : { spanEastM: 0, spanNorthM: 0 };
    out.push({
      id: el.id,
      geo,
      spanEastM: spans.spanEastM,
      spanNorthM: spans.spanNorthM,
      tags,
    });
  }
  return out;
}

function extractPolylines(doc: OsmDocument, kind: OsmPolyline["kind"], accept: (tags: Record<string, string>) => boolean, origin = ODESSA_ENU_ORIGIN): OsmPolyline[] {
  const out: OsmPolyline[] = [];
  for (const el of doc.elements) {
    const tags = el.tags ?? {};
    if (!accept(tags)) continue;
    const geometry = el.geometry ?? [];
    if (geometry.length < 2) continue;
    const points = geometry.map((p) => ({ lat: p.lat, lon: p.lon }));
    const bounds = elementBounds(el) ?? boundsFromGeometry(geometry);
    const spans = bounds ? footprintSpansM(bounds, origin) : { spanEastM: 0, spanNorthM: 0 };
    out.push({
      id: el.id,
      kind,
      points,
      lengthM: polylineLengthM(points, origin),
      spanEastM: spans.spanEastM,
      spanNorthM: spans.spanNorthM,
      tags,
    });
  }
  return out;
}

export function extractOsmRoads(doc: OsmDocument, origin = ODESSA_ENU_ORIGIN): OsmPolyline[] {
  return extractPolylines(doc, "road", (tags) => Boolean(tags.highway), origin);
}

export function extractOsmCoastline(doc: OsmDocument, origin = ODESSA_ENU_ORIGIN): OsmPolyline[] {
  return extractPolylines(
    doc,
    "coastline",
    (tags) => tags.natural === "coastline" || tags.waterway === "coastline" || tags.natural === "water",
    origin,
  );
}
