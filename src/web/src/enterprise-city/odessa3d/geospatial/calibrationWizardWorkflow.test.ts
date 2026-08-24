/**
 * STEP 30.1 — owner calibration wizard workflow.
 * Does not invent landmark GPS. Does not read city-plane coordinates as WGS84.
 */

import { describe, expect, it, beforeEach } from "vitest";
import {
  CITY_2D_MAP_IS_GEOGRAPHIC,
  applyGpsToSlot,
  applyMapAssistedPaste,
  applyPasteToGpsFields,
  buildAuthoredRecord,
  captureControlWorld,
  draftFromControlPoints,
  emptyCalibrationDraft,
  emptyCheckDraft,
  evaluateCalibrationDraft,
  evaluateCheckPoint,
  formatCalibrationSessionDebug,
  geoToWorld,
  isCollinearWorld,
  loadAuthoredCalibration,
  mapAssistedPickWorkflow,
  mapHelperOpenUrl,
  odessaMapHelperUrl,
  parseLatLonPair,
  resetAuthoredCalibration,
  resolveOdessaCalibration,
  saveAuthoredCalibration,
  solveCalibrationWithAxisInference,
  validateGpsInput,
  worldPairDistances,
  worldTriangleArea,
  worldToGeo,
  IDENTITY_AXIS_MAPPING,
} from "./index";
import { applyGpsPasteToSlot } from "./calibrationSession";
import { ODESSA_ENU_ORIGIN } from "./localMeters";
import type { AuthoredCalibrationRecord, GeoCalibration, GeoControlPoint } from "./types";
import type { CalibrationStorage } from "./calibrationStore";

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

function pointsFromTruth(
  truth: GeoCalibration,
  geos: Array<{ lat: number; lon: number }>,
  ids = ["A", "B", "C"],
): GeoControlPoint[] {
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
const GEO_CHECK = { lat: ODESSA_ENU_ORIGIN.lat + 0.002, lon: ODESSA_ENU_ORIGIN.lon - 0.002 };

describe("point picking stores intersection.point", () => {
  it("keeps the exact raycast world XYZ, not a centroid", () => {
    const hit = { x: 118.456, y: 7.891, z: -44.123 };
    const cap = captureControlWorld(hit, []);
    expect(cap.ok).toBe(true);
    if (!cap.ok) return;
    expect(cap.world).toEqual(hit);
    expect(cap.world.x).not.toBe(0);
    expect(cap.world).not.toEqual({ x: 0, y: 0, z: 0 });
  });
});

describe("GPS parser", () => {
  it("splits comma format", () => {
    const p = parseLatLonPair("46.482526, 30.723309");
    expect(p).toEqual({ latText: "46.482526", lonText: "30.723309" });
    const applied = applyPasteToGpsFields("46.482526, 30.723309", "");
    expect(applied.latText).toBe("46.482526");
    expect(applied.lonText).toBe("30.723309");
  });

  it("splits space format", () => {
    const p = parseLatLonPair("46.482526 30.723309");
    expect(p).toEqual({ latText: "46.482526", lonText: "30.723309" });
  });

  it("rejects invalid latitude", () => {
    expect(validateGpsInput("91", "30.72").error).toBe("latitude_out_of_range");
    expect(applyGpsPasteToSlot("91", "30.72", []).ok).toBe(false);
  });

  it("rejects invalid longitude", () => {
    expect(validateGpsInput("46.48", "200").error).toBe("longitude_out_of_range");
    expect(applyGpsToSlot("46.48", "181", []).ok).toBe(false);
  });
});

describe("A/B/C workflow", () => {
  it("advances from empty draft to three complete control points", () => {
    const truth = sampleCal();
    const pts = pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]);
    let draft = emptyCalibrationDraft();
    expect(evaluateCalibrationDraft(draft).complete).toHaveLength(0);

    draft = draftFromControlPoints([pts[0]]);
    expect(evaluateCalibrationDraft(draft).complete).toHaveLength(1);
    expect(evaluateCalibrationDraft(draft).canSave).toBe(false);

    draft = draftFromControlPoints([pts[0], pts[1]]);
    expect(evaluateCalibrationDraft(draft).provisionalStatus).toBe("PROVISIONAL");
    expect(evaluateCalibrationDraft(draft).canSave).toBe(false);

    draft = draftFromControlPoints(pts);
    const ev = evaluateCalibrationDraft(draft);
    expect(ev.complete.map((p) => p.id)).toEqual(["A", "B", "C"]);
    expect(ev.canSave).toBe(true);
  });
});

describe("spatial validation", () => {
  it("computes triangle area", () => {
    const area = worldTriangleArea({ x: 0, y: 0, z: 0 }, { x: 10, y: 0, z: 0 }, { x: 0, y: 0, z: 10 });
    expect(area).toBeCloseTo(50);
  });

  it("warns when A/B/C are collinear", () => {
    const draft = emptyCalibrationDraft();
    draft.A.world = { x: 0, y: 1, z: 0 };
    draft.B.world = { x: 100, y: 1, z: 0 };
    draft.C.world = { x: 200, y: 1, z: 0 };
    expect(isCollinearWorld(draft.A.world, draft.B.world, draft.C.world)).toBe(true);
    expect(evaluateCalibrationDraft(draft).collinear).toBe(true);
    expect(evaluateCalibrationDraft(draft).triangleArea).toBeCloseTo(0);
  });

  it("reports model-space A-B / A-C / B-C distances", () => {
    const draft = emptyCalibrationDraft();
    draft.A.world = { x: 0, y: 0, z: 0 };
    draft.B.world = { x: 80, y: 0, z: 0 };
    draft.C.world = { x: 0, y: 0, z: 60 };
    const d = worldPairDistances(draft);
    expect(d.ab).toBeCloseTo(80);
    expect(d.ac).toBeCloseTo(60);
    expect(d.bc).toBeCloseTo(100);
  });
});

describe("solver preview", () => {
  it("exposes residuals, scale, rotation, and quality without saving", () => {
    const truth = sampleCal();
    const draft = draftFromControlPoints(pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]));
    const ev = evaluateCalibrationDraft(draft);
    expect(ev.final?.calibration).toBeTruthy();
    expect(ev.final?.meanErrorMeters).toBeLessThan(2);
    expect(ev.final?.maxErrorMeters).toBeLessThan(5);
    expect(ev.final?.scale).toBeGreaterThan(0);
    expect(ev.final?.rotation).toBeTypeOf("number");
    expect(ev.final?.quality).toMatch(/EXCELLENT|GOOD|ACCEPTABLE/);
    expect(ev.canSave).toBe(true);
  });
});

describe("CHECK hold-out", () => {
  it("excludes CHECK from the solver control points", () => {
    const truth = sampleCal();
    const pts = pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]);
    const draft = draftFromControlPoints(pts);
    const check = {
      ...emptyCheckDraft(),
      world: geoToWorld(GEO_CHECK, truth),
      geo: GEO_CHECK,
    };
    const ev = evaluateCalibrationDraft(draft);
    expect(ev.complete).toHaveLength(3);
    expect(ev.complete.some((p) => p.id === "CHECK")).toBe(false);
    const chk = evaluateCheckPoint(check, ev.final);
    expect(chk.includedInSolver).toBe(false);
  });

  it("computes an independent CHECK error in meters", () => {
    const truth = sampleCal();
    const pts = pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]);
    const ev = evaluateCalibrationDraft(draftFromControlPoints(pts));
    const world = geoToWorld(GEO_CHECK, truth);
    const predicted = worldToGeo(world, ev.final!.calibration!);
    const actual = { lat: GEO_CHECK.lat + 0.00002, lon: GEO_CHECK.lon };
    const chk = evaluateCheckPoint({ world, geo: actual, latText: "", lonText: "" }, ev.final);
    expect(chk.predicted?.lat).toBeCloseTo(predicted.lat, 5);
    expect(chk.errorMeters ?? 0).toBeGreaterThan(1);
    expect(chk.errorMeters ?? 99).toBeLessThan(10);
    expect(chk.includedInSolver).toBe(false);
  });
});

describe("save / load / fingerprint / reset", () => {
  let storage: CalibrationStorage;

  beforeEach(() => {
    storage = mem();
  });

  function makeRecord(fp = "odessa:wizard"): AuthoredCalibrationRecord {
    const pts = pointsFromTruth(sampleCal(), [GEO_A, GEO_B, GEO_C]);
    const solved = solveCalibrationWithAxisInference(pts, "AUTHORED_CONTROL_POINTS");
    const record = buildAuthoredRecord({
      solve: solved,
      controlPoints: pts,
      modelFingerprint: fp,
    });
    if (!record) throw new Error("expected record");
    return record;
  }

  it("saves READY_CALIBRATED", () => {
    const record = makeRecord();
    expect(saveAuthoredCalibration(record, storage)).toBe(true);
    const resolved = resolveOdessaCalibration({
      saved: loadAuthoredCalibration(storage),
      currentFingerprint: "odessa:wizard",
    });
    expect(resolved.status).toBe("READY_CALIBRATED");
  });

  it("reloads READY_CALIBRATED when the fingerprint matches", () => {
    saveAuthoredCalibration(makeRecord("odessa:same"), storage);
    const resolved = resolveOdessaCalibration({
      saved: loadAuthoredCalibration(storage),
      currentFingerprint: "odessa:same",
    });
    expect(resolved.status).toBe("READY_CALIBRATED");
    expect(resolved.calibration).not.toBeNull();
  });

  it("rejects a fingerprint mismatch", () => {
    saveAuthoredCalibration(makeRecord("odessa:old"), storage);
    const resolved = resolveOdessaCalibration({
      saved: loadAuthoredCalibration(storage),
      currentFingerprint: "odessa:new",
    });
    expect(resolved.status).toBe("CALIBRATION_MODEL_MISMATCH");
    expect(resolved.calibration).toBeNull();
  });

  it("reset removes v2 calibration only", () => {
    saveAuthoredCalibration(makeRecord(), storage);
    resetAuthoredCalibration(storage);
    expect(loadAuthoredCalibration(storage)).toBeNull();
    expect(
      resolveOdessaCalibration({
        saved: loadAuthoredCalibration(storage),
        manifest: { calibrated: false },
      }).status,
    ).toBe("CALIBRATION_REQUIRED");
  });
});

describe("2D assisted point selection", () => {
  it("does not treat the Enterprise City plane map as WGS84", () => {
    expect(CITY_2D_MAP_IS_GEOGRAPHIC).toBe(false);
    expect(mapAssistedPickWorkflow()).toBe("osm-helper-paste");
  });

  it("opens an Odessa map helper without assigning coordinates", () => {
    const url = mapHelperOpenUrl();
    expect(url).toBe(odessaMapHelperUrl());
    expect(url).toContain("openstreetmap.org");
    expect(url).toContain(String(ODESSA_ENU_ORIGIN.lat));
    expect(url).toContain(String(ODESSA_ENU_ORIGIN.lon));
  });

  it("fills lat/lon from a pasted helper-map pair", () => {
    const pasted = applyMapAssistedPaste("46.482526, 30.723309");
    expect(pasted).toEqual({ latText: "46.482526", lonText: "30.723309" });
    const applied = applyGpsPasteToSlot(pasted!.latText, pasted!.lonText, []);
    expect(applied.ok).toBe(true);
    if (applied.ok) {
      expect(applied.geo.lat).toBeCloseTo(46.482526);
      expect(applied.geo.lon).toBeCloseTo(30.723309);
    }
  });
});

describe("debug session dump", () => {
  it("lists A/B/C world+GPS, distances, triangle, and CHECK fields", () => {
    const truth = sampleCal();
    const draft = draftFromControlPoints(pointsFromTruth(truth, [GEO_A, GEO_B, GEO_C]));
    const check = {
      ...emptyCheckDraft(),
      world: geoToWorld(GEO_CHECK, truth),
      geo: GEO_CHECK,
    };
    const text = formatCalibrationSessionDebug(draft, check);
    expect(text).toContain("A WORLD");
    expect(text).toContain("A GPS");
    expect(text).toContain("B WORLD");
    expect(text).toContain("C GPS");
    expect(text).toContain("AB distance");
    expect(text).toContain("triangle area");
    expect(text).toContain("CHECK predicted GPS");
    expect(text).toContain("CHECK error");
  });
});
