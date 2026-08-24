/**
 * STEP 29 — WGS84 ↔ local meters ↔ world, calibration, bounds, anchors.
 */

import { describe, expect, it, beforeEach } from "vitest";
import {
  wgs84ToLocalMeters,
  localMetersToWgs84,
  ODESSA_ENU_ORIGIN,
  geoToWorld,
  worldToGeo,
  IDENTITY_AXIS_MAPPING,
  solveCalibrationFromControlPoints,
  resolveOdessaCalibration,
  qualityFromError,
  classifyGeoAgainstBounds,
  worldBoxToGeoBounds,
  cityEntityToGeoAnchor,
  collectEnterpriseAnchors,
  isPureWgs84,
  overlaysEnabled,
  formatLatLon,
} from "./index";
import type { GeoCalibration, GeoControlPoint } from "./types";
import { clearCityEntities, listCityEntities, seedPlatformBuildingEntities, registerCityEntity } from "../cityEntityRegistry";
import { ODESSA_CITY } from "@/runtime/spatialRuntime/spatialTypes";
import { planeToGeo } from "@/runtime/spatialRuntime/spatialRegistry";

const ROUND_TRIP_M = 0.15;
const ROUND_TRIP_WORLD = 0.05;

function sampleCal(overrides: Partial<GeoCalibration> = {}): GeoCalibration {
  return {
    origin: { ...ODESSA_ENU_ORIGIN },
    worldOrigin: { x: 12, y: 1, z: -8 },
    metersPerWorldUnit: 1,
    rotationRadians: 0,
    axisMapping: IDENTITY_AXIS_MAPPING,
    source: "test",
    confidence: "EXACT",
    ...overrides,
  };
}

describe("WGS84 ↔ local meters", () => {
  it("maps the ENU origin to zeros", () => {
    const m = wgs84ToLocalMeters(ODESSA_ENU_ORIGIN);
    expect(m.east).toBeCloseTo(0, 8);
    expect(m.north).toBeCloseTo(0, 8);
    expect(m.up).toBeCloseTo(0, 8);
  });

  it("does not treat degrees as meters", () => {
    const north = wgs84ToLocalMeters({ lat: ODESSA_ENU_ORIGIN.lat + 0.01, lon: ODESSA_ENU_ORIGIN.lon });
    expect(north.north).toBeGreaterThan(1000);
    expect(Math.abs(north.east)).toBeLessThan(2);
  });

  it("round-trips geo → meters → geo at city scale", () => {
    const geo = { lat: 46.49, lon: 30.74, altitude: 18 };
    const meters = wgs84ToLocalMeters(geo);
    const back = localMetersToWgs84(meters);
    const err = wgs84ToLocalMeters({ lat: back.lat, lon: back.lon, altitude: back.altitude });
    const orig = wgs84ToLocalMeters(geo);
    expect(Math.hypot(err.east - orig.east, err.north - orig.north, err.up - orig.up)).toBeLessThan(ROUND_TRIP_M);
  });

  it("round-trips meters → geo → meters", () => {
    const meters = { east: 420, north: -310, up: 12 };
    const geo = localMetersToWgs84(meters);
    const back = wgs84ToLocalMeters(geo);
    expect(Math.hypot(back.east - meters.east, back.north - meters.north, back.up - meters.up)).toBeLessThan(ROUND_TRIP_M);
  });
});

describe("world transform", () => {
  it("round-trips geo → world → geo", () => {
    const cal = sampleCal({ rotationRadians: 0.4, metersPerWorldUnit: 1.15 });
    const geo = { lat: 46.487, lon: 30.73, altitude: 9 };
    const world = geoToWorld(geo, cal);
    const back = worldToGeo(world, cal);
    const w2 = geoToWorld(back, cal);
    expect(Math.hypot(w2.x - world.x, w2.y - world.y, w2.z - world.z)).toBeLessThan(ROUND_TRIP_WORLD);
  });

  it("round-trips world → geo → world", () => {
    const cal = sampleCal();
    const world = { x: 40, y: 6, z: -25 };
    const geo = worldToGeo(world, cal);
    const back = geoToWorld(geo, cal);
    expect(Math.hypot(back.x - world.x, back.y - world.y, back.z - world.z)).toBeLessThan(ROUND_TRIP_WORLD);
  });

  it("applies rotation", () => {
    const cal0 = sampleCal({ rotationRadians: 0, worldOrigin: { x: 0, y: 0, z: 0 } });
    const cal90 = sampleCal({ rotationRadians: Math.PI / 2, worldOrigin: { x: 0, y: 0, z: 0 } });
    const geo = { lat: ODESSA_ENU_ORIGIN.lat + 0.001, lon: ODESSA_ENU_ORIGIN.lon };
    const a = geoToWorld(geo, cal0);
    const b = geoToWorld(geo, cal90);
    expect(a.z).toBeGreaterThan(50);
    expect(b.x).toBeLessThan(-50);
    expect(Math.abs(a.x)).toBeLessThan(5);
  });

  it("applies uniform scale", () => {
    const cal1 = sampleCal({ metersPerWorldUnit: 1, worldOrigin: { x: 0, y: 0, z: 0 } });
    const cal2 = sampleCal({ metersPerWorldUnit: 2, worldOrigin: { x: 0, y: 0, z: 0 } });
    const geo = { lat: ODESSA_ENU_ORIGIN.lat + 0.001, lon: ODESSA_ENU_ORIGIN.lon };
    const a = geoToWorld(geo, cal1);
    const b = geoToWorld(geo, cal2);
    expect(a.z / b.z).toBeCloseTo(2, 5);
  });

  it("applies axis mapping east=+X north=−Z", () => {
    const cal = sampleCal({
      worldOrigin: { x: 0, y: 0, z: 0 },
      axisMapping: { east: "x", north: "-z", up: "y" },
    });
    const north = geoToWorld({ lat: ODESSA_ENU_ORIGIN.lat + 0.001, lon: ODESSA_ENU_ORIGIN.lon }, cal);
    expect(north.z).toBeLessThan(-50);
    const east = geoToWorld({ lat: ODESSA_ENU_ORIGIN.lat, lon: ODESSA_ENU_ORIGIN.lon + 0.001 }, cal);
    expect(east.x).toBeGreaterThan(50);
  });

  it("preserves altitude on Y", () => {
    const cal = sampleCal({ worldOrigin: { x: 0, y: 4, z: 0 }, metersPerWorldUnit: 1 });
    const w = geoToWorld({ ...ODESSA_ENU_ORIGIN, altitude: 10 }, cal);
    expect(w.y).toBeCloseTo(14, 5);
  });
});

describe("calibration status", () => {
  it("is CALIBRATION_REQUIRED without control points and does not fabricate a transform", () => {
    const r = resolveOdessaCalibration({
      manifest: { originLat: 46.4825, originLng: 30.7233, calibrated: false },
    });
    expect(r.status).toBe("CALIBRATION_REQUIRED");
    expect(r.calibration).toBeNull();
    expect(overlaysEnabled(r.status)).toBe(false);
    expect(r.reasons.some((x) => x.includes("no_control_points") || x.includes("calibrated_false"))).toBe(true);
  });

  it("does not treat manifest calibrated:true as enough without world origin/scale/rotation", () => {
    const r = resolveOdessaCalibration({
      manifest: { originLat: 46.4825, originLng: 30.7233, calibrated: true },
    });
    expect(r.status).toBe("CALIBRATION_REQUIRED");
    expect(r.calibration).toBeNull();
  });

  it("classifies residual quality bands", () => {
    expect(qualityFromError(1.2, 0.8)).toBe("EXCELLENT");
    expect(qualityFromError(2, 1)).toBe("GOOD");
    expect(qualityFromError(12, 5)).toBe("ACCEPTABLE");
    expect(qualityFromError(30, 12)).toBe("POOR");
    expect(qualityFromError(80, 40)).toBe("POOR");
    expect(qualityFromError(Number.NaN, 1)).toBe("INVALID");
  });
});

describe("control-point solver", () => {
  it("recovers translation, rotation, and uniform scale from 2 points", () => {
    const truth = sampleCal({
      rotationRadians: 0.35,
      metersPerWorldUnit: 0.95,
      worldOrigin: { x: 30, y: 2, z: -15 },
    });
    const a: GeoControlPoint = {
      id: "a",
      geo: { ...ODESSA_ENU_ORIGIN },
      world: geoToWorld({ ...ODESSA_ENU_ORIGIN }, truth),
    };
    const bGeo = { lat: ODESSA_ENU_ORIGIN.lat + 0.004, lon: ODESSA_ENU_ORIGIN.lon + 0.005 };
    const b: GeoControlPoint = { id: "b", geo: bGeo, world: geoToWorld(bGeo, truth) };
    const solved = solveCalibrationFromControlPoints([a, b]);
    expect(solved.status).toBe("PROVISIONAL");
    expect(solved.calibration).not.toBeNull();
    expect(solved.meanErrorMeters ?? 99).toBeLessThan(1);
    expect(solved.maxErrorMeters ?? 99).toBeLessThan(2);
    expect(solved.scale ?? 0).toBeCloseTo(1 / truth.metersPerWorldUnit, 2);
  });

  it("reports residuals with a third validation point", () => {
    const truth = sampleCal({ rotationRadians: -0.2, metersPerWorldUnit: 1 });
    const geos = [
      { ...ODESSA_ENU_ORIGIN },
      { lat: ODESSA_ENU_ORIGIN.lat + 0.003, lon: ODESSA_ENU_ORIGIN.lon + 0.002 },
      { lat: ODESSA_ENU_ORIGIN.lat - 0.002, lon: ODESSA_ENU_ORIGIN.lon + 0.004 },
    ];
    const points = geos.map((geo, i) => ({
      id: `p${i}`,
      geo,
      world: geoToWorld(geo, truth),
    }));
    const solved = solveCalibrationFromControlPoints(points);
    expect(solved.controlPointCount).toBe(3);
    expect(solved.maxErrorMeters ?? 99).toBeLessThan(1);
    expect(solved.quality).toMatch(/EXCELLENT|GOOD/);
  });

  it("rejects a single control point and coincident points", () => {
    const one = solveCalibrationFromControlPoints([
      { id: "a", geo: { ...ODESSA_ENU_ORIGIN }, world: { x: 0, y: 0, z: 0 } },
    ]);
    expect(one.status).toBe("CALIBRATION_REQUIRED");
    expect(one.calibration).toBeNull();
    const same = solveCalibrationFromControlPoints([
      { id: "a", geo: { ...ODESSA_ENU_ORIGIN }, world: { x: 0, y: 0, z: 0 } },
      { id: "b", geo: { ...ODESSA_ENU_ORIGIN }, world: { x: 1, y: 0, z: 1 } },
    ]);
    expect(same.status).toBe("INVALID");
  });
});

describe("bounds classification", () => {
  it("classifies IN / NEAR / OUT", () => {
    const cal = sampleCal({ worldOrigin: { x: 0, y: 0, z: 0 } });
    const bounds = worldBoxToGeoBounds(
      { min: { x: -100, y: 0, z: -100 }, max: { x: 100, y: 20, z: 100 } },
      cal,
    );
    const inside = worldToGeo({ x: 0, y: 0, z: 0 }, cal);
    expect(classifyGeoAgainstBounds(inside, bounds)).toBe("IN_BOUNDS");
    const edgeWorld = geoToWorld(
      { lat: bounds.north + (bounds.north - bounds.south) * 0.05, lon: (bounds.east + bounds.west) / 2 },
      cal,
    );
    const near = worldToGeo(edgeWorld, cal);
    expect(classifyGeoAgainstBounds(near, bounds)).toBe("NEAR_BOUNDS");
    const far = { lat: 47.2, lon: 31.5 };
    expect(classifyGeoAgainstBounds(far, bounds)).toBe("OUT_OF_BOUNDS");
  });
});

describe("enterprise geo anchors", () => {
  beforeEach(() => {
    clearCityEntities();
  });

  it("does not fabricate anchors from city-plane planeToGeo buildings", () => {
    seedPlatformBuildingEntities();
    const plane = planeToGeo(10, 20);
    expect(isPureWgs84(plane)).toBe(false);
    const anchors = collectEnterpriseAnchors(listCityEntities());
    const buildingAnchors = anchors.filter((a) => a.type === "enterprise");
    expect(buildingAnchors).toHaveLength(0);
  });

  it("accepts only pure WGS84 entity coordinates", () => {
    registerCityEntity({
      id: "city_building_crm",
      kind: "building",
      label: "CRM Center",
      geo: { lat: 46.48, lng: 30.73, x: 10, y: 18 },
    });
    expect(cityEntityToGeoAnchor(listCityEntities()[0])).toBeNull();
    registerCityEntity({
      id: ODESSA_CITY.id,
      kind: "marker",
      label: ODESSA_CITY.nameUk,
      geo: { lat: ODESSA_CITY.lat, lng: ODESSA_CITY.lng },
    });
    const city = listCityEntities().find((e) => e.id === ODESSA_CITY.id);
    const anchor = city ? cityEntityToGeoAnchor(city) : null;
    expect(anchor?.coordinate.lat).toBe(ODESSA_CITY.lat);
    expect(anchor?.coordinate.lon).toBe(ODESSA_CITY.lng);
  });
});

describe("copy format", () => {
  it("formats lat, lon with 6 decimals", () => {
    expect(formatLatLon({ lat: 46.1234567, lon: 30.1234567 })).toBe("46.123457, 30.123457");
  });
});
