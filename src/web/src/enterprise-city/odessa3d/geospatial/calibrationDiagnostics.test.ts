/**
 * STEP 30.2 — diagnosable georeference. Does not invent landmark GPS.
 */

import { describe, expect, it } from "vitest";
import {
  AUTHORED_CALIBRATION_STORAGE_KEY,
  IDENTITY_AXIS_MAPPING,
  IDENTITY_MODEL_ROOT,
  PICK_COORDINATE_SPACE,
  RAW_OBSERVATIONS_STORAGE_KEY,
  buildAuthoredRecord,
  classifyScaleStatus,
  controlHorizontalResiduals,
  draftFromObservations,
  evaluateCheckForensics,
  formatGeoreferenceDiagnosticV3,
  geoToWorld,
  leaveOneOut,
  loadRawObservations,
  pairScaleRows,
  resetAuthoredCalibration,
  saveRawObservations,
  solveCalibrationWithAxisInference,
  emptyCalibrationDraft,
  emptyCheckDraft,
  draftFromControlPoints,
} from "./index";
import type { GeoCalibration, GeoControlPoint } from "./types";
import { ODESSA_ENU_ORIGIN } from "./localMeters";
import type { CalibrationStorage } from "./calibrationStore";

function truth(scale = 1, rotation = 0, worldOrigin = { x: 40, y: 2, z: -10 }): GeoCalibration {
  return {
    origin: { ...ODESSA_ENU_ORIGIN },
    worldOrigin,
    metersPerWorldUnit: 1 / scale,
    rotationRadians: rotation,
    axisMapping: IDENTITY_AXIS_MAPPING,
    source: "test",
    confidence: "CALIBRATED",
  };
}

const GEO_A = { ...ODESSA_ENU_ORIGIN };
const GEO_B = { lat: ODESSA_ENU_ORIGIN.lat + 0.004, lon: ODESSA_ENU_ORIGIN.lon + 0.005 };
const GEO_C = { lat: ODESSA_ENU_ORIGIN.lat - 0.003, lon: ODESSA_ENU_ORIGIN.lon + 0.003 };
const GEO_K = { lat: ODESSA_ENU_ORIGIN.lat + 0.002, lon: ODESSA_ENU_ORIGIN.lon - 0.002 };

function pts(cal: GeoCalibration, geos = [GEO_A, GEO_B, GEO_C], ids = ["A", "B", "C"]): GeoControlPoint[] {
  return geos.map((geo, i) => ({
    id: ids[i],
    label: ids[i],
    geo,
    world: geoToWorld(geo, cal),
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

describe("STEP 30.2 known scale=1 + independent CHECK", () => {
  it("recovers identity transform and near-zero CHECK error", () => {
    const cal = truth(1, 0);
    const controls = pts(cal);
    const solved = solveCalibrationWithAxisInference(controls);
    expect(solved.calibration).not.toBeNull();
    expect(solved.scale ?? 0).toBeCloseTo(1, 2);
    expect(solved.meanErrorMeters ?? 9).toBeLessThan(0.2);
    const checkWorld = geoToWorld(GEO_K, cal);
    const chk = evaluateCheckForensics(
      { world: checkWorld, geo: GEO_K, latText: "", lonText: "" },
      controls,
      solved.calibration,
    );
    expect(chk.includedInSolver).toBe(false);
    expect(chk.errorM ?? 9).toBeLessThan(0.25);
    expect(solved.controlPointCount).toBe(3);
  });
});

describe("STEP 30.2 known scale=1.5", () => {
  it("recovers approximately 1.5 world units per meter", () => {
    const cal = truth(1.5, 0.12);
    const solved = solveCalibrationWithAxisInference(pts(cal));
    expect(solved.scale ?? 0).toBeCloseTo(1.5, 2);
  });
});

describe("STEP 30.2 leave-one-out", () => {
  it("flags an intentionally corrupted control point", () => {
    const cal = truth(1, 0);
    const controls = pts(cal);
    controls[2] = {
      ...controls[2],
      geo: { lat: GEO_C.lat + 0.004, lon: GEO_C.lon - 0.004 },
    };
    const loo = leaveOneOut(controls);
    expect(loo.abToCErrorM ?? 0).toBeGreaterThan(100);
    expect(loo.likelyBadPoint).toBe("C");
  });
});

describe("STEP 30.2 horizontal vs Y", () => {
  it("does not let different world Y change horizontal RMS", () => {
    const cal = truth(1, 0);
    const base = pts(cal);
    const tall = base.map((p, i) => ({ ...p, world: { ...p.world, y: p.world.y + i * 25 } }));
    const solvedBase = solveCalibrationWithAxisInference(base);
    const solvedTall = solveCalibrationWithAxisInference(tall);
    expect(solvedBase.calibration).not.toBeNull();
    expect(solvedTall.calibration).not.toBeNull();
    const h0 = controlHorizontalResiduals(base, solvedBase.calibration!, geoToWorld);
    const h1 = controlHorizontalResiduals(tall, solvedTall.calibration!, geoToWorld);
    const rms = (rows: typeof h0) => Math.sqrt(rows.reduce((s, r) => s + r.horizontalM ** 2, 0) / rows.length);
    expect(Math.abs(rms(h0) - rms(h1))).toBeLessThan(0.05);
    expect(solvedTall.maxErrorMeters3d ?? 0).toBeGreaterThan(solvedBase.maxErrorMeters3d ?? 0);
    expect(solvedTall.quality).toBe(solvedBase.quality);
  });
});

describe("pair scale + persist raw observations", () => {
  it("reports WORLD_UNITS_PER_METER pair scales", () => {
    const cal = truth(1.2, 0);
    const rows = pairScaleRows(pts(cal));
    expect(rows).toHaveLength(3);
    for (const row of rows) {
      expect(row.convention).toBe("WORLD_UNITS_PER_METER");
      expect(row.worldUnitsPerMeter ?? 0).toBeCloseTo(1.2, 2);
    }
    expect(classifyScaleStatus(rows, 1.2)).toBe("CONSISTENT_WITH_SOLVER");
  });

  it("reloads A/B/C raw observations after reset-free persist", () => {
    const storage = mem();
    const cal = truth(1, 0);
    const controls = pts(cal);
    saveRawObservations(
      {
        modelRoot: IDENTITY_MODEL_ROOT,
        observations: controls.map((p) => ({
          id: p.id,
          world: p.world,
          gps: p.geo,
          pickedAt: "2026-08-23T00:00:00.000Z",
          coordinateSpace: "world",
        })),
        check: { id: "CHECK", world: geoToWorld(GEO_K, cal), gps: GEO_K, pickedAt: null, coordinateSpace: "world" },
      },
      storage,
    );
    expect(storage.getItem(RAW_OBSERVATIONS_STORAGE_KEY)).toBeTruthy();
    const loaded = loadRawObservations(storage);
    expect(loaded?.observations).toHaveLength(3);
    const draft = draftFromObservations(loaded!.observations);
    expect(draft.A.world).toEqual(controls[0].world);
    expect(draft.A.geo).toEqual(controls[0].geo);
    expect(loaded?.check?.gps).toEqual(GEO_K);
    resetAuthoredCalibration(storage);
    expect(loadRawObservations(storage)).toBeNull();
  });

  it("migrates v2 authored control points into raw observations", () => {
    const storage = mem();
    const cal = truth(1, 0);
    const controls = pts(cal);
    const solved = solveCalibrationWithAxisInference(controls);
    const record = buildAuthoredRecord({
      solve: solved,
      controlPoints: controls,
      modelFingerprint: "odessa:v2-migrate",
    });
    if (!record) throw new Error("expected record");
    const { observations: _obs, schemaVersion: _sv, ...rest } = record;
    storage.setItem(AUTHORED_CALIBRATION_STORAGE_KEY, JSON.stringify({ ...rest, version: 2 }));
    const loaded = loadRawObservations(storage);
    expect(loaded?.observations).toHaveLength(3);
    expect(loaded?.observations[0].gps).toEqual(controls[0].geo);
    expect(loaded?.observations[0].world).toEqual(controls[0].world);
  });
});

describe("V3 diagnostic dump", () => {
  it("contains required keys and excludes CHECK from solver points", () => {
    const cal = truth(1, 0);
    const draft = draftFromControlPoints(pts(cal));
    const check = { ...emptyCheckDraft(), world: geoToWorld(GEO_K, cal), geo: GEO_K };
    const text = formatGeoreferenceDiagnosticV3({
      draft,
      check,
      modelRoot: IDENTITY_MODEL_ROOT,
      pickCoordinateSpace: PICK_COORDINATE_SPACE,
    });
    const required = [
      "=== GEOREFERENCE DIAGNOSTIC V3 ===",
      "A_WORLD=",
      "A_GPS=",
      "A_HORIZONTAL_RESIDUAL_M=",
      "B_WORLD=",
      "B_GPS=",
      "B_HORIZONTAL_RESIDUAL_M=",
      "C_WORLD=",
      "C_GPS=",
      "C_HORIZONTAL_RESIDUAL_M=",
      "CONTROL_HORIZONTAL_RMS_M=",
      "CONTROL_HORIZONTAL_MAX_M=",
      "CONTROL_3D_RMS_M=",
      "CONTROL_3D_MAX_M=",
      "AB_WORLD_HORIZONTAL_DISTANCE=",
      "AB_GPS_DISTANCE_M=",
      "AB_SCALE=",
      "AC_WORLD_HORIZONTAL_DISTANCE=",
      "AC_GPS_DISTANCE_M=",
      "AC_SCALE=",
      "BC_WORLD_HORIZONTAL_DISTANCE=",
      "BC_GPS_DISTANCE_M=",
      "BC_SCALE=",
      "AB_TO_C_ERROR_M=",
      "AC_TO_B_ERROR_M=",
      "BC_TO_A_ERROR_M=",
      "LIKELY_BAD_POINT=",
      "PACKAGE_SCALE_EXPECTED=",
      "SOLVER_SCALE=",
      "SCALE_STATUS=",
      "CURRENT_AXIS_MAPPING=",
      "BEST_AXIS_MAPPING=",
      "BEST_AXIS_HORIZONTAL_RMS=",
      "PICK_COORDINATE_SPACE=threejs-world",
      "MODEL_ROOT_POSITION=",
      "MODEL_ROOT_ROTATION=",
      "MODEL_ROOT_SCALE=",
      "CHECK_WORLD=",
      "CHECK_ACTUAL_GPS=",
      "CHECK_PREDICTED_GPS=",
      "CHECK_ERROR_M=",
      "CHECK_EAST_ERROR_M=",
      "CHECK_NORTH_ERROR_M=",
      "AB_SOLVER_TO_CHECK_ERROR_M=",
      "AC_SOLVER_TO_CHECK_ERROR_M=",
      "BC_SOLVER_TO_CHECK_ERROR_M=",
      "=== END GEOREFERENCE DIAGNOSTIC V3 ===",
    ];
    for (const key of required) expect(text).toContain(key);
    expect(emptyCalibrationDraft().A.pickedAt).toBeNull();
  });
});
