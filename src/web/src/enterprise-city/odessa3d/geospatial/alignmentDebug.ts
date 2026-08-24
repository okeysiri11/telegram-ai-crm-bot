/**
 * Top-down alignment debug drawing. Metadata only — does not change city geometry.
 */

import type { GeoCalibration, GeoCoordinate, LocalWorldCoordinate } from "./types";
import { geoToWorld } from "./worldTransform";
import { UNCALIBRATED_GEOTRANSFORM_AXES } from "./worldTransform";
import { ODESSA_ENU_ORIGIN } from "./localMeters";
import type { GeometricMatchCandidate } from "./geometricMatching";
import type { ModelXzSignature } from "./modelSignatures";
import type { OsmBuildingFootprint, OsmPolyline } from "./osmGeometry";

export type AlignmentDebugInput = {
  model: readonly ModelXzSignature[];
  osmBuildings: readonly OsmBuildingFootprint[];
  osmRoads?: readonly OsmPolyline[];
  osmCoast?: readonly OsmPolyline[];
  accepted: readonly GeometricMatchCandidate[];
  rejected: readonly GeometricMatchCandidate[];
  residuals?: ReadonlyArray<{ from: LocalWorldCoordinate; to: LocalWorldCoordinate }>;
  checkWorld?: LocalWorldCoordinate | null;
  calibration?: GeoCalibration | null;
};

const PREVIEW_CAL: GeoCalibration = {
  origin: { ...ODESSA_ENU_ORIGIN },
  worldOrigin: { x: 0, y: 0, z: 0 },
  metersPerWorldUnit: 1,
  rotationRadians: 0,
  axisMapping: UNCALIBRATED_GEOTRANSFORM_AXES,
  source: "DEBUG_PREVIEW_IDENTITY_ENU_NOT_A_SOLVE",
  confidence: "UNAVAILABLE",
};

function esc(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c] ?? c));
}

function osmToWorld(geo: GeoCoordinate, calibration: GeoCalibration | null): LocalWorldCoordinate {
  return geoToWorld(geo, calibration ?? PREVIEW_CAL);
}

export function buildAlignmentDebugSvg(input: AlignmentDebugInput): string {
  const cal = input.calibration ?? PREVIEW_CAL;
  const pts: Array<{ x: number; z: number }> = [];
  for (const m of input.model) pts.push({ x: m.world.x, z: m.world.z });
  for (const o of input.osmBuildings) {
    const w = osmToWorld(o.geo, cal);
    pts.push({ x: w.x, z: w.z });
  }
  if (input.checkWorld) pts.push({ x: input.checkWorld.x, z: input.checkWorld.z });
  if (!pts.length) {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text x="8" y="20">NO_GEOMETRY</text></svg>`;
  }
  const xs = pts.map((p) => p.x);
  const zs = pts.map((p) => p.z);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minZ = Math.min(...zs);
  const maxZ = Math.max(...zs);
  const pad = 400;
  const w = Math.max(maxX - minX + pad * 2, 1000);
  const h = Math.max(maxZ - minZ + pad * 2, 1000);
  const sx = (x: number) => x - minX + pad;
  const sz = (z: number) => z - minZ + pad;
  const parts: string[] = [];
  parts.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w.toFixed(1)} ${h.toFixed(1)}" width="1600" height="1200">`);
  parts.push(`<rect width="100%" height="100%" fill="#0b1220"/>`);
  parts.push(`<text x="24" y="36" fill="#d7e3ff" font-size="28">STEP 30.5 alignment debug (top-down X/Z)</text>`);
  parts.push(
    `<text x="24" y="68" fill="#8aa0c8" font-size="16">OSM preview uses ${esc(cal.source)} — not a production lock. Green=accepted, red=rejected, cyan=model, gray=OSM, orange=residual, magenta=CHECK.</text>`,
  );
  for (const m of input.model) {
    const color = m.class === "building" ? "#4cc3ff" : m.class === "road" ? "#7d8ea8" : m.class === "water" ? "#1b6b9a" : "#5a6a80";
    const opacity = m.cityWide ? 0.12 : 0.45;
    parts.push(
      `<rect x="${(sx(m.world.x) - m.spanX / 2).toFixed(1)}" y="${(sz(m.world.z) - m.spanZ / 2).toFixed(1)}" width="${Math.max(m.spanX, 8).toFixed(1)}" height="${Math.max(m.spanZ, 8).toFixed(1)}" fill="${color}" fill-opacity="${opacity}" stroke="${color}" stroke-opacity="0.8" stroke-width="2"/>`,
    );
  }
  for (const o of input.osmBuildings) {
    const wld = osmToWorld(o.geo, cal);
    parts.push(`<circle cx="${sx(wld.x).toFixed(1)}" cy="${sz(wld.z).toFixed(1)}" r="6" fill="#9aa4b5" fill-opacity="0.35"/>`);
  }
  for (const r of input.rejected) {
    parts.push(`<circle cx="${sx(r.world.x).toFixed(1)}" cy="${sz(r.world.z).toFixed(1)}" r="10" fill="#ff4d4d" fill-opacity="0.7"/>`);
  }
  for (const a of input.accepted) {
    const pred = osmToWorld(a.geo, cal);
    parts.push(`<circle cx="${sx(a.world.x).toFixed(1)}" cy="${sz(a.world.z).toFixed(1)}" r="12" fill="#3dff8a"/>`);
    parts.push(
      `<line x1="${sx(a.world.x).toFixed(1)}" y1="${sz(a.world.z).toFixed(1)}" x2="${sx(pred.x).toFixed(1)}" y2="${sz(pred.z).toFixed(1)}" stroke="#ffb020" stroke-width="3"/>`,
    );
  }
  for (const res of input.residuals ?? []) {
    parts.push(
      `<line x1="${sx(res.from.x).toFixed(1)}" y1="${sz(res.from.z).toFixed(1)}" x2="${sx(res.to.x).toFixed(1)}" y2="${sz(res.to.z).toFixed(1)}" stroke="#ffb020" stroke-width="2"/>`,
    );
  }
  if (input.checkWorld) {
    parts.push(
      `<circle cx="${sx(input.checkWorld.x).toFixed(1)}" cy="${sz(input.checkWorld.z).toFixed(1)}" r="16" fill="none" stroke="#ff37d4" stroke-width="4"/>`,
    );
    parts.push(
      `<text x="${(sx(input.checkWorld.x) + 20).toFixed(1)}" y="${sz(input.checkWorld.z).toFixed(1)}" fill="#ff37d4" font-size="20">HISTORICAL CHECK</text>`,
    );
  }
  parts.push(`</svg>`);
  return parts.join("");
}

export function buildMatchesJson(input: {
  osmSource: string;
  osmBuildingCount: number;
  osmRoadCount: number;
  modelBuildingCandidates: number;
  modelRoadCandidates: number;
  accepted: readonly GeometricMatchCandidate[];
  rejected: readonly GeometricMatchCandidate[];
  rawCount: number;
}): Record<string, unknown> {
  return {
    step: "30.5",
    osmSource: input.osmSource,
    osmBuildingCount: input.osmBuildingCount,
    osmRoadCount: input.osmRoadCount,
    modelBuildingCandidates: input.modelBuildingCandidates,
    modelRoadCandidates: input.modelRoadCandidates,
    rawMatches: input.rawCount,
    accepted: input.accepted.map((m) => ({
      model: m.modelName,
      osmId: m.osmId,
      kind: m.kind,
      reason: m.reason,
      world: m.world,
      geo: m.geo,
      modelFootprint: m.modelFootprint,
      osmFootprint: m.osmFootprint,
    })),
    rejected: input.rejected.slice(0, 200).map((m) => ({
      model: m.modelName,
      osmId: m.osmId,
      kind: m.kind,
      reason: m.reason,
      world: m.world,
      geo: m.geo,
      modelFootprint: m.modelFootprint,
      osmFootprint: m.osmFootprint,
    })),
    rejectedTruncated: input.rejected.length > 200,
  };
}
