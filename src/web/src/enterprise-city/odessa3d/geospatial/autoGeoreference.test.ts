/**
 * STEP 30.4 automated georeference. Does not invent operator A/B/C.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  CITED_ODESSA_PUBLIC_LANDMARKS,
  HISTORICAL_CHECK_ACTUAL_GPS,
  HISTORICAL_CHECK_WORLD,
  IDENTITY_AXIS_MAPPING,
  evaluateHistoricalCheck,
  extractModelLandmarks,
  geoToWorld,
  loadAuthoredCalibration,
  loadPublicLandmarkCache,
  mapLandmarksExact,
  matchableModelLandmarks,
  normalizeLandmarkName,
  parsePublicLandmarkCache,
  ransacSolveCalibration,
  runAutomatedGeoreference,
  solveCalibrationWithAxisInference,
} from "./index";
import type { GeoCalibration, GeoControlPoint } from "./types";
import { ODESSA_ENU_ORIGIN } from "./localMeters";
import type { CalibrationStorage } from "./calibrationStore";

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
    worldOrigin: { x: 10, y: 1, z: -4 },
    metersPerWorldUnit: 1 / scale,
    rotationRadians: 0,
    axisMapping: IDENTITY_AXIS_MAPPING,
    source: "test",
    confidence: "CALIBRATED",
  };
}

const GEO = [
  { ...ODESSA_ENU_ORIGIN },
  { lat: ODESSA_ENU_ORIGIN.lat + 0.003, lon: ODESSA_ENU_ORIGIN.lon + 0.004 },
  { lat: ODESSA_ENU_ORIGIN.lat - 0.002, lon: ODESSA_ENU_ORIGIN.lon + 0.003 },
  { lat: ODESSA_ENU_ORIGIN.lat + 0.001, lon: ODESSA_ENU_ORIGIN.lon - 0.002 },
];

function pts(cal: GeoCalibration, geos = GEO, ids = ["A", "B", "C", "CHECK"]): GeoControlPoint[] {
  return geos.map((geo, i) => ({
    id: ids[i],
    label: ids[i],
    geo,
    world: geoToWorld(geo, cal),
  }));
}

describe("public landmark parser/cache", () => {
  it("parses GeoJSON points and cited catalog", () => {
    const cache = parsePublicLandmarkCache({
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [30.741667, 46.485556] },
          properties: { name: "Odesa Opera and Ballet Theatre", id: "wiki-opera" },
        },
      ],
    });
    expect(cache.landmarks).toHaveLength(1);
    expect(cache.landmarks[0].gps.lat).toBeCloseTo(46.485556);
    expect(loadPublicLandmarkCache().length).toBeGreaterThanOrEqual(1);
    expect(CITED_ODESSA_PUBLIC_LANDMARKS[0].source).toMatch(/Wikidata/);
    expect(normalizeLandmarkName("WEB_name_Odesa_Opera_1")).toBe("odesa opera 1");
  });
});

describe("model landmarks + exact mapping", () => {
  it("does not treat generic WEB_build as a landmark", () => {
    const extracted = extractModelLandmarks([{ name: "WEB_build" }, { name: "WEB_name_Odesa_Opera_1", file: "t.glb" }]);
    expect(extracted.find((m) => m.name === "WEB_build")?.matchable).toBe(false);
    expect(matchableModelLandmarks([{ name: "WEB_name_Odesa_Opera_1" }])).toHaveLength(1);
  });

  it("maps only exact normalized names", () => {
    const mapped = mapLandmarksExact(CITED_ODESSA_PUBLIC_LANDMARKS, [
      { id: "WEB_name_Odesa_Opera", name: "WEB_name_Odesa_Opera", normalized: "odesa opera", world: { x: 1, y: 2, z: 3 }, source: "t", matchable: true },
    ]);
    expect(mapped).toHaveLength(1);
    expect(mapLandmarksExact(CITED_ODESSA_PUBLIC_LANDMARKS, matchableModelLandmarks([{ name: "WEB_name_FONTAN_SKY_1" }]))).toHaveLength(0);
  });
});

describe("similarity / axis / RANSAC / CHECK exclusion", () => {
  it("recovers scale and rejects a corrupted control", () => {
    const cal = truth(1.5);
    const controls = pts(cal, GEO.slice(0, 3));
    const solved = solveCalibrationWithAxisInference(controls);
    expect(solved.scale ?? 0).toBeCloseTo(1.5, 2);
    const dirty = [...controls];
    dirty[2] = { ...dirty[2], geo: { lat: GEO[2].lat + 0.01, lon: GEO[2].lon } };
    const ransac = ransacSolveCalibration([...dirty, pts(cal, [GEO[3]], ["D"])[0]], { residualThresholdM: 20 });
    expect(ransac.rejected.some((p) => p.id === "C") || ransac.inliers.every((p) => p.id !== "C")).toBe(true);
  });

  it("never adds historical CHECK to solver points", () => {
    const cal = truth(1);
    const controls = pts(cal, GEO.slice(0, 3));
    const chk = evaluateHistoricalCheck(cal, controls);
    expect(chk.includedInSolver).toBe(false);
    expect(controls.some((p) => p.id === "CHECK")).toBe(false);
    expect(HISTORICAL_CHECK_WORLD.x).toBeCloseTo(-1935.01);
    expect(HISTORICAL_CHECK_ACTUAL_GPS.lat).toBeCloseTo(46.386267);
  });
});

describe("v4 persist/reload + geometry invariance", () => {
  it("reloads the same transform from schema v4", () => {
    const cal = truth(1);
    const controls = pts(cal, GEO.slice(0, 3));
    const publicLm = [
      { id: "pA", name: "Alpha Landmark", aliases: [], gps: GEO[0], source: "test" },
      { id: "pB", name: "Bravo Landmark", aliases: [], gps: GEO[1], source: "test" },
      { id: "pC", name: "Charlie Landmark", aliases: [], gps: GEO[2], source: "test" },
    ];
    const inventory = [
      { name: "WEB_name_Alpha_Landmark", center: geoToWorld(GEO[0], cal) },
      { name: "WEB_name_Bravo_Landmark", center: geoToWorld(GEO[1], cal) },
      { name: "WEB_name_Charlie_Landmark", center: geoToWorld(GEO[2], cal) },
    ];
    const storage = mem();
    const result = runAutomatedGeoreference({
      inventory,
      publicLandmarks: publicLm,
      storage,
      modelFingerprint: "odessa:step30.4-test",
    });
    expect(result.semanticMappingFound).toBe(3);
    expect(result.persisted).toBe(true);
    expect(result.georeferenceStatus).toMatch(/EXCELLENT|GOOD|ACCEPTABLE/);
    const loaded = loadAuthoredCalibration(storage);
    expect(loaded?.version).toBe(4);
    expect(loaded?.scale).toBeCloseTo(result.solverScale ?? 0, 3);
    expect(loaded?.controlPoints).toHaveLength(3);
  });

  it("does not import geometry repair modules", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const src = readFileSync(join(here, "autoGeoreference.ts"), "utf8");
    expect(src).not.toMatch(/verticalRecovery|scenePrep|componentRepair/);
  });
});

describe("Odessa inventory has no semantic public mapping", () => {
  it("blocks automated georeference on the real mesh-name inventory", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const inventoryPath = join(here, "../../../../scripts/step29_6_inventory.json");
    const inventory = JSON.parse(readFileSync(inventoryPath, "utf8")) as Array<{ name: string }>;
    const result = runAutomatedGeoreference({ inventory });
    expect(result.publicLandmarksFound).toBeGreaterThan(0);
    expect(result.semanticMappingFound).toBe(0);
    expect(result.georeferenceStatus).toBe("BLOCKED");
    expect(result.persisted).toBe(false);
    expect(result.historicalCheckErrorM).toBeCloseTo(36.58, 1);
  });
});
