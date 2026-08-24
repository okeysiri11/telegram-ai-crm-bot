/**
 * STEP 29.1 — interactive 3-point calibration workflow.
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  IDENTITY_AXIS_MAPPING,
  UNCALIBRATED_GEOTRANSFORM_AXES,
  applyGpsToSlot,
  AUTHORED_CALIBRATION_STORAGE_KEY,
  buildAuthoredRecord,
  canPersistQuality,
  clickGeoEnabled,
  controlPointDistances,
  DEV_GEO_ANCHORS,
  captureControlWorld,
  copyCalibrationDebugData,
  draftFromControlPoints,
  emptyCalibrationDraft,
  evaluateCalibrationDraft,
  exportAuthoredCalibrationJson,
  geoToWorld,
  importAuthoredCalibrationJson,
  independentHoldoutResidual,
  loadAuthoredCalibration,
  odessaModelFingerprint,
  overlaysEnabled,
  parseAuthoredCalibrationJson,
  qualityFromError,
  resetAuthoredCalibration,
  resolveOdessaCalibration,
  saveAuthoredCalibration,
  solveCalibrationFromControlPoints,
  solveCalibrationWithAxisInference,
  validateGpsInput,
  worldToGeo,
  SATELLITE_REFERENCE,
  geoSelectionBridge,
  ODESSA_GEO_ORIGIN,
} from "./index";
import type { AuthoredCalibrationRecord, GeoCalibration, GeoControlPoint } from "./types";
import { ODESSA_ENU_ORIGIN } from "./localMeters";
import type { CalibrationStorage } from "./calibrationStore";

const ROUND_TRIP_WORLD = 0.05;

function sampleCal(overrides: Partial<GeoCalibration> = {}): GeoCalibration {
  return {
    origin: { ...ODESSA_ENU_ORIGIN },
    worldOrigin: { x: 12, y: 1, z: -8 },
    metersPerWorldUnit: 1,
    rotationRadians: 0.18,
    axisMapping: IDENTITY_AXIS_MAPPING,
    source: "test",
    confidence: "CALIBRATED",
    ...overrides,
  };
}

function pointsFromTruth(truth: GeoCalibration, geos: Array<{ lat: number; lon: number }>, ids = ["A", "B", "C"]): GeoControlPoint[] {
  return geos.map((geo, i) => ({
    id: ids[i] ?? `p${i}`,
    label: ids[i] ?? `p${i}`,
    geo,
    world: geoToWorld(geo, truth),
  }));
}

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

const GEO_A = { ...ODESSA_ENU_ORIGIN };
const GEO_B = { lat: ODESSA_ENU_ORIGIN.lat + 0.004, lon: ODESSA_ENU_ORIGIN.lon + 0.005 };
const GEO_C = { lat: ODESSA_ENU_ORIGIN.lat - 0.003, lon: ODESSA_ENU_ORIGIN.lon + 0.003 };

describe("control point capture", () => {
  it("records finite world points and rejects duplicates", () => {
    const a = captureControlWorld({ x: 10, y: 2, z: -4 }, []);
    expect(a.ok).toBe(true);
    const dup = captureControlWorld({ x: 10.4, y: 3, z: -4.2 }, [a.ok ? a.world : null]);
    expect(dup.ok).toBe(false);
    expect(dup.ok === false && dup.error).toBe("duplicate_world_point");
    const b = captureControlWorld({ x: 80, y: 2, z: 40 }, [a.ok ? a.world : null]);
    expect(b.ok).toBe(true);
  });

  it("rejects non-finite intersection points", () => {
    expect(captureControlWorld({ x: Number.NaN, y: 0, z: 0 }, []).ok).toBe(false);
  });
});

describe("GPS validation", () => {
  it("accepts Odessa-range coordinates", () => {
    const r = validateGpsInput("46.4825", "30.7233");
    expect(r.ok).toBe(true);
    expect(r.geo?.lat).toBeCloseTo(46.4825);
  });

  it("rejects invalid numbers and ranges", () => {
    expect(validateGpsInput("", "30").ok).toBe(false);
    expect(validateGpsInput("abc", "30").ok).toBe(false);
    expect(validateGpsInput("91", "30").error).toBe("latitude_out_of_range");
    expect(validateGpsInput("46", "200").error).toBe("longitude_out_of_range");
  });

  it("rejects coordinates outside the Odessa range", () => {
    const r = validateGpsInput("50.45", "30.52");
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/outside_odessa_range/);
  });
});

describe("duplicate GPS points", () => {
  it("rejects a second GPS within 20 m", () => {
    const r = applyGpsToSlot("46.4825", "30.7233", [ODESSA_ENU_ORIGIN]);
    expect(r.ok).toBe(false);
    expect(r.ok === false && r.error).toBe("duplicate_gps_point");
  });
});

describe("two-point similarity solve", () => {
  it("recovers rotation, uniform scale, and translation", () => {
    const truth = sampleCal({
      rotationRadians: 0.41,
      metersPerWorldUnit: 0.92,
      worldOrigin: { x: 40, y: 2, z: -22 },
    });
    const pts = pointsFromTruth(truth, [GEO_A, GEO_B], ["A", "B"]);
    const solved = solveCalibrationFromControlPoints(pts);
    expect(solved.calibration).not.toBeNull();
    expect(solved.scale ?? 0).toBeCloseTo(1 / truth.metersPerWorldUnit, 2);
    expect(solved.meanErrorMeters ?? 99).toBeLessThan(1);
  });
});

describe("axis / sign inference", () => {
  it("selects east=+X north=−Z when that is the true mapping", () => {
    const truth = sampleCal({
      axisMapping: UNCALIBRATED_GEOTRANSFORM_AXES,
      rotationRadians: 0.05,
      metersPerWorldUnit: 1,
    });
    const pts = pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]);
    const identity = solveCalibrationFromControlPoints(pts, "t", IDENTITY_AXIS_MAPPING);
    const inferred = solveCalibrationWithAxisInference(pts);
    expect(inferred.calibration?.axisMapping.north).toBe("-z");
    expect(inferred.calibration?.axisMapping.east).toBe("x");
    expect(inferred.meanErrorMeters ?? 99).toBeLessThan(identity.meanErrorMeters ?? 99);
    expect(inferred.meanErrorMeters ?? 99).toBeLessThan(1);
  });
});

describe("rotation / scale / translation", () => {
  it("solves each component from three known points", () => {
    const truth = sampleCal({
      rotationRadians: -0.33,
      metersPerWorldUnit: 1.2,
      worldOrigin: { x: -15, y: 3, z: 28 },
    });
    const pts = pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]);
    const solved = solveCalibrationWithAxisInference(pts);
    expect(solved.calibration).not.toBeNull();
    expect(solved.scale ?? 0).toBeCloseTo(1 / truth.metersPerWorldUnit, 2);
    expect(solved.rotation ?? 99).toBeCloseTo(truth.rotationRadians, 2);
    expect(solved.meanErrorMeters ?? 99).toBeLessThan(1);
  });
});

describe("degenerate pair rejection", () => {
  it("rejects world-coincident and geo-coincident pairs", () => {
    const geoClose = solveCalibrationFromControlPoints([
      { id: "A", geo: GEO_A, world: { x: 0, y: 0, z: 0 } },
      { id: "B", geo: GEO_A, world: { x: 80, y: 0, z: 80 } },
    ]);
    expect(geoClose.status).toBe("INVALID");
    expect(geoClose.reasons.some((r) => r.includes("degenerate_pair") || r.includes("too_close"))).toBe(true);

    const worldClose = solveCalibrationFromControlPoints([
      { id: "A", geo: GEO_A, world: { x: 0, y: 0, z: 0 } },
      { id: "B", geo: GEO_B, world: { x: 0.4, y: 0, z: 0.4 } },
    ]);
    expect(worldClose.status).toBe("INVALID");
  });
});

describe("provisional status and independent residual", () => {
  it("marks two complete points as provisional and hold-out tests C", () => {
    const truth = sampleCal();
    const pts = pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]);
    const draft = draftFromControlPoints(pts);
    const ev = evaluateCalibrationDraft(draft);
    expect(ev.provisionalStatus).toBe("PROVISIONAL");
    expect(ev.provisional?.calibration).not.toBeNull();
    expect(ev.independentResidualMeters ?? 99).toBeLessThan(2);
    expect(ev.final?.controlPointCount).toBe(3);
    expect(ev.canSave).toBe(true);
  });

  it("does not allow save with only two points", () => {
    const truth = sampleCal();
    const draft = draftFromControlPoints(pointsFromTruth(truth, [GEO_A, GEO_B], ["A", "B"]));
    const ev = evaluateCalibrationDraft(draft);
    expect(ev.provisionalStatus).toBe("PROVISIONAL");
    expect(ev.canSave).toBe(false);
  });

  it("computes an independent residual without fitting C", () => {
    const truth = sampleCal();
    const [a, b, c] = pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]);
    const err = independentHoldoutResidual([a, b], c);
    expect(err ?? 99).toBeLessThan(2);
  });
});

describe("least-squares final calibration and quality", () => {
  it("fits three points and classifies quality", () => {
    const truth = sampleCal();
    const solved = solveCalibrationWithAxisInference(pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]));
    expect(solved.quality).toMatch(/EXCELLENT|GOOD|ACCEPTABLE/);
    expect(qualityFromError(1.2, 0.8)).toBe("EXCELLENT");
    expect(qualityFromError(4, 2)).toBe("GOOD");
    expect(qualityFromError(12, 6)).toBe("ACCEPTABLE");
    expect(qualityFromError(30, 12)).toBe("POOR");
  });
});

describe("save / load / fingerprint / reset", () => {
  let storage: CalibrationStorage;

  beforeEach(() => {
    storage = mem();
  });

  function makeRecord(fp = "odessa:test"): AuthoredCalibrationRecord {
    const truth = sampleCal();
    const pts = pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]);
    const solved = solveCalibrationWithAxisInference(pts, "AUTHORED_CONTROL_POINTS");
    const record = buildAuthoredRecord({
      solve: solved,
      controlPoints: pts,
      modelFingerprint: fp,
    });
    if (!record) throw new Error("expected record");
    return record;
  }

  it("persists authored calibration and restores READY_CALIBRATED", () => {
    const record = makeRecord("odessa:abc");
    expect(saveAuthoredCalibration(record, storage)).toBe(true);
    const loaded = loadAuthoredCalibration(storage);
    expect(loaded?.source).toBe("AUTHORED_CONTROL_POINTS");
    expect(loaded?.confidence).toBe("CALIBRATED");
    const resolved = resolveOdessaCalibration({
      saved: loaded,
      currentFingerprint: "odessa:abc",
    });
    expect(resolved.status).toBe("READY_CALIBRATED");
    expect(overlaysEnabled(resolved.status)).toBe(true);
    expect(resolved.calibration?.source).toBe("AUTHORED_CONTROL_POINTS");
  });

  it("sets CALIBRATION_MODEL_MISMATCH when the model fingerprint changes", () => {
    const record = makeRecord("odessa:old");
    saveAuthoredCalibration(record, storage);
    const resolved = resolveOdessaCalibration({
      saved: loadAuthoredCalibration(storage),
      currentFingerprint: "odessa:new",
    });
    expect(resolved.status).toBe("CALIBRATION_MODEL_MISMATCH");
    expect(resolved.calibration).toBeNull();
    expect(overlaysEnabled(resolved.status)).toBe(false);
  });

  it("reset removes authored calibration only", () => {
    storage.setItem("crm.unrelated", "keep");
    saveAuthoredCalibration(makeRecord(), storage);
    resetAuthoredCalibration(storage);
    expect(loadAuthoredCalibration(storage)).toBeNull();
    expect(storage.getItem("crm.unrelated")).toBe("keep");
    const resolved = resolveOdessaCalibration({
      saved: loadAuthoredCalibration(storage),
      manifest: { calibrated: false },
    });
    expect(resolved.status).toBe("CALIBRATION_REQUIRED");
  });
});

describe("JSON export / import", () => {
  it("round-trips a valid record and rejects invalid JSON", () => {
    const truth = sampleCal();
    const pts = pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]);
    const solved = solveCalibrationWithAxisInference(pts, "AUTHORED_CONTROL_POINTS");
    const record = buildAuthoredRecord({
      solve: solved,
      controlPoints: pts,
      modelFingerprint: "odessa:json",
    });
    if (!record) throw new Error("expected record");
    const json = exportAuthoredCalibrationJson(record);
    const parsed = importAuthoredCalibrationJson(json);
    expect(parsed.ok).toBe(true);
    if (parsed.ok) {
      expect(parsed.record.controlPoints).toHaveLength(3);
      expect(parsed.record.axisMapping).toEqual(record.axisMapping);
    }
    expect(parseAuthoredCalibrationJson("not-json").ok).toBe(false);
    expect(parseAuthoredCalibrationJson("[]").ok).toBe(false);
    expect(parseAuthoredCalibrationJson(JSON.stringify({ version: 2 })).ok).toBe(false);
    expect(parseAuthoredCalibrationJson(JSON.stringify({ version: 1, source: "x" })).ok).toBe(false);
  });
});

describe("round-trip after calibration", () => {
  it("world ↔ geo stays tight after a saved solve", () => {
    const truth = sampleCal({ rotationRadians: 0.22, metersPerWorldUnit: 1.05 });
    const pts = pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]);
    const solved = solveCalibrationWithAxisInference(pts);
    expect(solved.calibration).not.toBeNull();
    const cal = solved.calibration!;
    const geo = { lat: 46.49, lon: 30.74 };
    const world = geoToWorld(geo, cal);
    const back = worldToGeo(world, cal);
    const world2 = geoToWorld(back, cal);
    expect(Math.hypot(world2.x - world.x, world2.y - world.y, world2.z - world.z)).toBeLessThan(ROUND_TRIP_WORLD);
  });
});

describe("model fingerprint", () => {
  it("is stable for the same manifest and changes when the model changes", () => {
    const a = odessaModelFingerprint({
      cityId: "odessa",
      version: "1",
      tiles: [{ id: "t1" }, { id: "t2" }],
      stats: { asset_count: 45 },
      cityBounds: { minX: -1, maxX: 1, minZ: -1, maxZ: 1 },
    });
    const b = odessaModelFingerprint({
      cityId: "odessa",
      version: "1",
      tiles: [{ id: "t1" }, { id: "t2" }],
      stats: { asset_count: 45 },
      cityBounds: { minX: -1, maxX: 1, minZ: -1, maxZ: 1 },
    });
    const c = odessaModelFingerprint({
      cityId: "odessa",
      version: "2",
      tiles: [{ id: "t1" }, { id: "t2" }],
      stats: { asset_count: 45 },
      cityBounds: { minX: -1, maxX: 1, minZ: -1, maxZ: 1 },
    });
    expect(a).toBe(b);
    expect(a).not.toBe(c);
  });
});

describe("copy debug data", () => {
  it("emits label, world XYZ, and lat/lon", () => {
    const text = copyCalibrationDebugData({
      id: "A",
      label: "A",
      world: { x: 1.25, y: 2.5, z: 3.75 },
      geo: { lat: 46.4825, lon: 30.7233 },
      latText: "46.4825",
      lonText: "30.7233",
      pickedAt: null,
    });
    expect(text).toContain("Label: A");
    expect(text).toContain("World X: 1.250");
    expect(text).toContain("Latitude: 46.482500");
    expect(text).toContain("Longitude: 30.723300");
  });
});

describe("satellite reference architecture", () => {
  it("does not enable an external map provider", () => {
    expect(SATELLITE_REFERENCE.enabled).toBe(false);
    expect(SATELLITE_REFERENCE.provider).toBeNull();
  });
});

describe("empty draft", () => {
  it("starts with no complete points", () => {
    const ev = evaluateCalibrationDraft(emptyCalibrationDraft());
    expect(ev.complete).toHaveLength(0);
    expect(ev.provisionalStatus).toBe("NONE");
    expect(ev.canSave).toBe(false);
  });
});

describe("STEP 30 georeference contract", () => {
  it("keeps GeoOrigin as math reference, not a model lock", () => {
    expect(ODESSA_GEO_ORIGIN.referenceLat).toBeCloseTo(46.4825);
    expect(ODESSA_GEO_ORIGIN.referenceLon).toBeCloseTo(30.7233);
    expect(DEV_GEO_ANCHORS[0]?.metadata?.notALandmark).toBe(true);
  });

  it("disables click geo before READY and enables after", () => {
    expect(clickGeoEnabled("CALIBRATION_REQUIRED")).toBe(false);
    expect(clickGeoEnabled("PROVISIONAL")).toBe(false);
    expect(clickGeoEnabled("CALIBRATION_POOR")).toBe(false);
    expect(clickGeoEnabled("READY_CALIBRATED")).toBe(true);
  });

  it("does not persist POOR without explicit allowPoor", () => {
    expect(canPersistQuality("POOR")).toBe(false);
    expect(canPersistQuality("POOR", true)).toBe(true);
  });

  it("reports A/B/C distances and writes v2 storage key", () => {
    const truth = sampleCal();
    const draft = draftFromControlPoints(pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]));
    const d = controlPointDistances(draft);
    expect(d.ab).toBeGreaterThan(20);
    expect(d.ac).toBeGreaterThan(20);
    expect(d.bc).toBeGreaterThan(20);
    const storage = mem();
    const solved = solveCalibrationWithAxisInference(pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]), "AUTHORED_CONTROL_POINTS");
    const record = buildAuthoredRecord({
      solve: solved,
      controlPoints: pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]),
      modelFingerprint: "odessa:v2",
    });
    expect(record?.version).toBe(3);
    expect(record?.geoOrigin).toBeTruthy();
    expect(saveAuthoredCalibration(record!, storage)).toBe(true);
    expect(storage.getItem(AUTHORED_CALIBRATION_STORAGE_KEY)).toBeTruthy();
  });

  it("bridges 2D ↔ 3D without inventing plane GPS", () => {
    geoSelectionBridge.clear();
    const geo = { lat: 46.49, lon: 30.74 };
    geoSelectionBridge.requestShowIn3d(geo);
    expect(geoSelectionBridge.get().intent).toBe("show-3d");
    expect(geoSelectionBridge.consumeShow3d()).toEqual(geo);
    geoSelectionBridge.requestShowIn2d(geo);
    expect(geoSelectionBridge.consumeShow2d()?.lat).toBeCloseTo(46.49);
  });
});
