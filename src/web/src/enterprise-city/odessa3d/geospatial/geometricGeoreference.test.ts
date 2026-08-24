/**
 * STEP 30.5 geometric georeference. Does not invent operator A/B/C.
 */

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";
import {
  CITYWIDE_SPAN_M,
  HISTORICAL_CHECK_ACTUAL_GPS,
  HISTORICAL_CHECK_WORLD,
  HISTORICAL_SOLVER_SCALE_1_4475,
  IDENTITY_AXIS_MAPPING,
  PACKAGE_SCALE_1_0,
  allPairWorldUnitsPerMeter,
  buildAlignmentDebugSvg,
  classifyModelName,
  coastlineMetric,
  constellationConsistent,
  extractOsmBuildings,
  extractOsmCoastline,
  extractOsmRoads,
  footprintsSimilar,
  geoToWorld,
  loadAuthoredCalibration,
  localBuildingSignatures,
  matchBuildings,
  matchRoads,
  orderedFootprint,
  parseModelSignatures,
  parseOsmDocument,
  pairScaleDistribution,
  polylineNearestRmsM,
  qualityFromIndependentCheck,
  ransacSolveCalibration,
  runGeometricGeoreference,
  scaleHypothesisSupported,
  searchAxisMappings,
  solveCalibrationWithAxisInference,
  spatialDistribution,
  uniqueBidirectionalMatches,
} from "./index";
import type { GeoCalibration, GeoControlPoint } from "./types";
import { ODESSA_ENU_ORIGIN, localMetersToWgs84, wgs84ToLocalMeters } from "./localMeters";
import type { CalibrationStorage } from "./calibrationStore";
import type { ModelXzSignature } from "./modelSignatures";
import type { OsmBuildingFootprint } from "./osmGeometry";

const here = dirname(fileURLToPath(import.meta.url));
const webRoot = join(here, "../../../..");
const repoRoot = join(webRoot, "../..");

function mem(): CalibrationStorage {
  const m = new Map<string, string>();
  return {
    getItem: (k) => m.get(k) ?? null,
    setItem: (k, v) => {
      m.set(k, v);
    },
    removeItem: (k) => {
      m.delete(k);
    },
  };
}

function truth(scale = 1): GeoCalibration {
  return {
    origin: { ...ODESSA_ENU_ORIGIN },
    worldOrigin: { x: 40, y: 2, z: -15 },
    metersPerWorldUnit: 1 / scale,
    rotationRadians: 0.02,
    axisMapping: IDENTITY_AXIS_MAPPING,
    source: "test",
    confidence: "CALIBRATED",
  };
}

const GEO = [
  { ...ODESSA_ENU_ORIGIN },
  { lat: ODESSA_ENU_ORIGIN.lat + 0.004, lon: ODESSA_ENU_ORIGIN.lon + 0.005 },
  { lat: ODESSA_ENU_ORIGIN.lat - 0.003, lon: ODESSA_ENU_ORIGIN.lon + 0.004 },
  { lat: ODESSA_ENU_ORIGIN.lat + 0.002, lon: ODESSA_ENU_ORIGIN.lon - 0.003 },
  { lat: ODESSA_ENU_ORIGIN.lat - 0.0015, lon: ODESSA_ENU_ORIGIN.lon - 0.004 },
];

function pts(cal: GeoCalibration, geos = GEO, ids = ["A", "B", "C", "D", "E"]): GeoControlPoint[] {
  return geos.map((geo, i) => ({
    id: ids[i],
    label: ids[i],
    geo,
    world: geoToWorld(geo, cal),
  }));
}

function modelAt(name: string, world: { x: number; y: number; z: number }, spanX: number, spanZ: number, cls: ModelXzSignature["class"] = "building"): ModelXzSignature {
  return {
    name,
    file: "t.glb",
    class: cls,
    world,
    spanX,
    spanY: 12,
    spanZ,
    cityWide: spanX > CITYWIDE_SPAN_M || spanZ > CITYWIDE_SPAN_M,
  };
}

function osmBuilding(id: number, geo: { lat: number; lon: number }, spanEastM: number, spanNorthM: number): OsmBuildingFootprint {
  return { id, geo, spanEastM, spanNorthM, tags: { building: "yes" } };
}

function osmWayFromFootprint(id: number, geo: { lat: number; lon: number }, spanEastM: number, spanNorthM: number) {
  const c = wgs84ToLocalMeters(geo);
  const sw = localMetersToWgs84({ east: c.east - spanEastM / 2, north: c.north - spanNorthM / 2, up: 0 });
  const ne = localMetersToWgs84({ east: c.east + spanEastM / 2, north: c.north + spanNorthM / 2, up: 0 });
  return {
    type: "way",
    id,
    center: { lat: geo.lat, lon: geo.lon },
    bounds: { minlat: sw.lat, maxlat: ne.lat, minlon: sw.lon, maxlon: ne.lon },
    tags: { building: "yes" },
  };
}

describe("OSM geometry parser", () => {
  it("parses buildings, roads, and coastline from Overpass JSON", () => {
    const raw = {
      elements: [
        {
          type: "way",
          id: 11,
          bounds: { minlat: 46.48, minlon: 30.72, maxlat: 46.4808, maxlon: 30.7212 },
          center: { lat: 46.4804, lon: 30.7206 },
          tags: { building: "yes" },
        },
        {
          type: "way",
          id: 22,
          geometry: [
            { lat: 46.48, lon: 30.72 },
            { lat: 46.481, lon: 30.721 },
          ],
          tags: { highway: "primary" },
        },
        {
          type: "way",
          id: 33,
          geometry: [
            { lat: 46.47, lon: 30.73 },
            { lat: 46.471, lon: 30.731 },
          ],
          tags: { natural: "coastline" },
        },
      ],
    };
    const doc = parseOsmDocument(raw);
    expect(doc.elements).toHaveLength(3);
    const buildings = extractOsmBuildings(doc);
    expect(buildings).toHaveLength(1);
    expect(buildings[0].spanEastM).toBeGreaterThan(50);
    expect(buildings[0].spanNorthM).toBeGreaterThan(50);
    expect(extractOsmRoads(doc)).toHaveLength(1);
    expect(extractOsmCoastline(doc)).toHaveLength(1);
  });
});

describe("model X/Z signature extraction", () => {
  it("classifies and keeps local building footprints only", () => {
    expect(classifyModelName("WEB_building12")).toBe("building");
    expect(classifyModelName("WEB_highway_primary_1")).toBe("road");
    expect(classifyModelName("WEB_water")).toBe("water");
    const doc = parseModelSignatures({
      rows: [
        { name: "WEB_build", cx: 0, cy: 1, cz: 0, dx: 40000, dy: 10, dz: 50000, class: "building" },
        { name: "WEB_building12", cx: 10, cy: 2, cz: 20, dx: 58, dy: 81, dz: 94, class: "building" },
      ],
    });
    expect(doc.buildings).toBe(2);
    expect(doc.rows[0].cityWide).toBe(true);
    expect(localBuildingSignatures(doc.rows)).toHaveLength(1);
    expect(localBuildingSignatures(doc.rows)[0].world.x).toBe(10);
  });
});

describe("axis mapping search + similarity + RANSAC", () => {
  it("recovers identity mapping and uniform scale", () => {
    const cal = truth(1);
    const controls = pts(cal, GEO.slice(0, 3));
    const solved = solveCalibrationWithAxisInference(controls);
    expect(solved.scale ?? 0).toBeCloseTo(1, 2);
    const axis = searchAxisMappings(controls);
    const best = [...axis].sort((a, b) => (a.horizontalRmsM ?? 1e9) - (b.horizontalRmsM ?? 1e9))[0];
    expect(best.mapping.east).toBe(IDENTITY_AXIS_MAPPING.east);
    expect(best.mapping.north).toBe(IDENTITY_AXIS_MAPPING.north);
  });

  it("RANSAC drops a corrupted control", () => {
    const cal = truth(1);
    const controls = pts(cal, GEO.slice(0, 4), ["A", "B", "C", "D"]);
    const dirty = [...controls];
    dirty[2] = { ...dirty[2], geo: { lat: GEO[2].lat + 0.02, lon: GEO[2].lon } };
    const ransac = ransacSolveCalibration(dirty, { residualThresholdM: 15 });
    expect(ransac.inliers.every((p) => p.id !== "C") || ransac.rejected.some((p) => p.id === "C")).toBe(true);
  });
});

describe("building / road matching + spatial distribution", () => {
  it("accepts only a unique consistent constellation", () => {
    const cal = truth(1);
    const worlds = GEO.slice(0, 4).map((g) => geoToWorld(g, cal));
    const footprints = [
      [40, 70],
      [55, 120],
      [90, 90],
      [22, 48],
    ] as const;
    const model = worlds.map((w, i) => modelAt(`B${i}`, w, footprints[i][0], footprints[i][1]));
    const osm = GEO.slice(0, 4).map((g, i) => osmBuilding(100 + i, g, footprints[i][0], footprints[i][1]));
    osm.push(osmBuilding(999, GEO[4], 18, 19));
    const matched = matchBuildings(model, osm);
    expect(matched.accepted.length).toBe(4);
    expect(constellationConsistent(matched.accepted)).toBe(true);
    const spatial = spatialDistribution(
      matched.accepted.map((m, i) => ({
        id: String(i),
        geo: m.geo,
        world: m.world,
      })),
    );
    expect(spatial.ok).toBe(true);
    expect(spatial.matchedRegionCount).toBeGreaterThanOrEqual(2);
  });

  it("rejects size-unique pairs that cannot form a 3-point constellation", () => {
    const model = [modelAt("ONLY", { x: 0, y: 0, z: 0 }, 141, 150), modelAt("OTHER", { x: 9000, y: 0, z: 2000 }, 14, 74)];
    const osm = [osmBuilding(1, ODESSA_ENU_ORIGIN, 141, 150), osmBuilding(2, GEO[1], 14, 74)];
    const matched = matchBuildings(model, osm);
    expect(matched.accepted).toHaveLength(0);
    expect(matched.rejected.some((r) => r.reason.includes("constellation") || r.reason.includes("scale"))).toBe(true);
  });

  it("matches unique local roads the same way", () => {
    const cal = truth(1);
    const worlds = GEO.slice(0, 3).map((g) => geoToWorld(g, cal));
    const model = worlds.map((w, i) => modelAt(`R${i}`, w, 80 + i * 10, 400 + i * 20, "road"));
    const osmDoc = {
      elements: GEO.slice(0, 3).map((g, i) => ({
        type: "way",
        id: 50 + i,
        geometry: [
          { lat: g.lat - 0.001, lon: g.lon - 0.0004 },
          { lat: g.lat + 0.001, lon: g.lon + 0.0004 },
        ],
        bounds: {
          minlat: g.lat - 0.0018,
          maxlat: g.lat + 0.0018,
          minlon: g.lon - 0.0005 - i * 0.00005,
          maxlon: g.lon + 0.0005 + i * 0.00005,
        },
        tags: { highway: "primary" },
      })),
    };
    const roads = extractOsmRoads(parseOsmDocument(osmDoc));
    const matched = matchRoads(model, roads, 0.35);
    expect(matched.accepted.length + matched.rejected.length).toBeGreaterThan(0);
  });
});

describe("coastline metric", () => {
  it("reports RMS between two nearby polylines and blocks city-wide water AABBs", () => {
    const a = [
      { lat: 46.48, lon: 30.72 },
      { lat: 46.481, lon: 30.721 },
    ];
    const b = [
      { lat: 46.48002, lon: 30.72002 },
      { lat: 46.48102, lon: 30.72102 },
    ];
    expect(polylineNearestRmsM(a, b)).toBeLessThan(10);
    const metric = coastlineMetric(
      [modelAt("WEB_water", { x: 0, y: 0, z: 0 }, 60000, 90000, "water")],
      extractOsmCoastline(
        parseOsmDocument({
          elements: [{ type: "way", id: 1, geometry: a, tags: { natural: "coastline" } }],
        }),
      ),
      null,
    );
    expect(metric.available).toBe(false);
    expect(metric.precisionNote).toMatch(/CITYWIDE|AABB/);
  });
});

describe("pair-scale distribution + held-out validation", () => {
  it("supports scale 1.0 and rejects 1.4475 on a 1:1 constellation", () => {
    const cal = truth(1);
    const points = pts(cal);
    const dist = pairScaleDistribution(points);
    expect(dist.count).toBe(allPairWorldUnitsPerMeter(points).length);
    expect(dist.count).toBeGreaterThanOrEqual(6);
    expect(scaleHypothesisSupported(dist, PACKAGE_SCALE_1_0)).toBe(true);
    expect(scaleHypothesisSupported(dist, HISTORICAL_SOLVER_SCALE_1_4475)).toBe(false);
  });

  it("supports 1.4475 only when pair scales actually sit there", () => {
    const cal = truth(1.4475);
    const dist = pairScaleDistribution(pts(cal));
    expect(scaleHypothesisSupported(dist, HISTORICAL_SOLVER_SCALE_1_4475)).toBe(true);
    expect(scaleHypothesisSupported(dist, PACKAGE_SCALE_1_0)).toBe(false);
  });

  it("held-out independent check is EXCELLENT on synthetic truth", () => {
    const cal = truth(1);
    const worlds = GEO.map((g) => geoToWorld(g, cal));
    const footprints = [
      [32, 60],
      [48, 88],
      [70, 110],
      [25, 41],
      [95, 40],
    ] as const;
    const model = worlds.map((w, i) => modelAt(`S${i}`, w, footprints[i][0], footprints[i][1]));
    const osm = GEO.map((g, i) => osmBuilding(200 + i, g, footprints[i][0], footprints[i][1]));
    const result = runGeometricGeoreference({
      osmBuildingsDoc: {
        elements: osm.map((o) => osmWayFromFootprint(o.id, o.geo, o.spanEastM, o.spanNorthM)),
      },
      modelRows: model,
      storage: mem(),
      modelFingerprint: "odessa:step30.5-synthetic",
      includeHistoricalCheck: false,
    });
    expect(result.accepted.length).toBeGreaterThanOrEqual(4);
    expect(result.independentCheckCount).toBeGreaterThanOrEqual(1);
    expect(result.georeferenceStatus).toMatch(/EXCELLENT|GOOD|ACCEPTABLE/);
    expect(qualityFromIndependentCheck(result.independentCheckRmsM, result.independentCheckP95M)).toMatch(
      /EXCELLENT|GOOD|ACCEPTABLE/,
    );
  });
});

describe("persistence / reload + geometry immutability", () => {
  it("reloads a persisted synthetic geometric solve and does not touch assets", () => {
    const cal = truth(1);
    const worlds = GEO.slice(0, 4).map((g) => geoToWorld(g, cal));
    const footprints = [
      [36, 64],
      [50, 92],
      [78, 100],
      [28, 44],
    ] as const;
    const model = worlds.map((w, i) => modelAt(`P${i}`, w, footprints[i][0], footprints[i][1]));
    const storage = mem();
    const manifestPath = join(webRoot, "public/assets/odessa_metric/odessa_manifest.json");
    const before = createHash("sha256").update(readFileSync(manifestPath)).digest("hex");
    const result = runGeometricGeoreference({
      osmBuildingsDoc: {
        elements: GEO.slice(0, 4).map((g, i) => osmWayFromFootprint(300 + i, g, footprints[i][0], footprints[i][1])),
      },
      modelRows: model,
      storage,
      modelFingerprint: "odessa:step30.5-persist",
      includeHistoricalCheck: false,
    });
    expect(result.geometryChanged).toBe(false);
    expect(result.step29RepairChanged).toBe(false);
    expect(result.persisted).toBe(true);
    const loaded = loadAuthoredCalibration(storage);
    expect(loaded?.version).toBe(4);
    expect(loaded?.scale).toBeCloseTo(result.solverScale ?? 0, 2);
    const after = createHash("sha256").update(readFileSync(manifestPath)).digest("hex");
    expect(after).toBe(before);
    const src = readFileSync(join(here, "geometricGeoreference.ts"), "utf8");
    expect(src).not.toMatch(/verticalRecovery|scenePrep|componentRepair|writeFileSync/);
  });
});

describe("Odessa live OSM + model signatures", () => {
  it("does not invent a lock and writes debug artifacts", () => {
    const signatures = JSON.parse(readFileSync(join(webRoot, "scripts/step30_5_model_signatures.json"), "utf8"));
    const buildings = JSON.parse(readFileSync(join(here, "osm_cache/buildings_bb.json"), "utf8"));
    const roads = JSON.parse(readFileSync(join(here, "osm_cache/roads.json"), "utf8"));
    const coast = JSON.parse(readFileSync(join(here, "osm_cache/coastline.json"), "utf8"));
    const result = runGeometricGeoreference({
      osmBuildingsDoc: buildings,
      osmRoadsDoc: roads,
      osmCoastDoc: coast,
      modelSignatures: signatures,
      osmSource: "overpass-api.de",
      includeHistoricalCheck: true,
    });
    expect(result.osmBuildingCount).toBeGreaterThan(2000);
    expect(result.osmRoadCount).toBeGreaterThan(100);
    expect(result.modelBuildingCandidates).toBeGreaterThan(10);
    expect(result.accepted.length).toBe(0);
    expect(result.persisted).toBe(false);
    expect(result.georeferenceStatus).toBe("BLOCKED");
    expect(result.safeToStartStep31).toBe(false);
    expect(result.geometryChanged).toBe(false);
    expect(result.scale14475Supported).toBe(false);
    expect(result.scale10Supported).toBe(false);
    expect(result.historicalCheckErrorM).toBeCloseTo(36.58, 1);
    expect(HISTORICAL_CHECK_WORLD.x).toBeCloseTo(-1935.01);
    expect(HISTORICAL_CHECK_ACTUAL_GPS.lat).toBeCloseTo(46.386267);
    expect(result.debugSvg).toContain("<svg");
    writeFileSync(join(repoRoot, "docs/STEP_30_5_ALIGNMENT_DEBUG.svg"), result.debugSvg);
    writeFileSync(join(repoRoot, "docs/STEP_30_5_MATCHES.json"), JSON.stringify(result.matchesJson, null, 2));
    expect(result.coastlineMatchAvailable).toBe(false);
    expect(footprintsSimilar(orderedFootprint(10, 20), orderedFootprint(11, 19), 0.15)).toBe(true);
    expect(uniqueBidirectionalMatches([]).unique).toHaveLength(0);
  });
});

describe("debug drawing", () => {
  it("renders a top-down svg", () => {
    const svg = buildAlignmentDebugSvg({
      model: [modelAt("WEB_building12", { x: 100, y: 0, z: 200 }, 58, 94)],
      osmBuildings: [osmBuilding(1, ODESSA_ENU_ORIGIN, 58, 94)],
      accepted: [],
      rejected: [],
      checkWorld: HISTORICAL_CHECK_WORLD,
    });
    expect(svg).toContain("HISTORICAL CHECK");
  });
});
