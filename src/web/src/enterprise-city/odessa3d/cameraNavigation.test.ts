import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  BASE_PAN_SPEED,
  CAMERA_DAMPING_FACTOR,
  CAMERA_MIN_DISTANCE_M,
  CAMERA_MIN_HEIGHT_ABOVE_BASE_M,
  CAMERA_NEAR_MAX,
  CAMERA_NEAR_MIN,
  CAMERA_POLAR_2D_MAX,
  CAMERA_POLAR_2D_MIN,
  CAMERA_POLAR_3D_MAX,
  CAMERA_POLAR_3D_MIN,
  CITY_SCREEN_SPACE_PANNING,
  CITY_ZOOM_TOWARD_POINTER,
  HOME_TWEEN_MS,
  LOGARITHMIC_DEPTH_BUFFER,
  applyCameraGroundConstraint,
  computeAdaptiveCameraClip,
  computeCameraClipRange,
  distancePanCompensation,
  panSpeedForDistance,
} from "./cameraNavigation";
import { polarLimitsForViewMode, topDownPose } from "./cameraViewMode";
import { isCityDebugEnabled } from "./cityDebug";
import { computeGlobalCityBounds, fitCameraToOdessaBounds } from "./cityAssembly";
import type { CityBounds } from "./types";

const ODESSA_BOUNDS: CityBounds = {
  minX: -417.79,
  maxX: 317.64,
  minZ: -389.48,
  maxZ: 658.09,
  minY: -0.16,
  maxY: 1.99,
};

describe("Odessa camera clip range", () => {
  it("computes near in CAMERA_NEAR_MIN–MAX from current city bounds, not a tiny hardcoded near", () => {
    const g = computeGlobalCityBounds([], ODESSA_BOUNDS);
    const clip = computeCameraClipRange(g);
    expect(clip.near).toBeGreaterThanOrEqual(CAMERA_NEAR_MIN);
    expect(clip.near).toBeLessThanOrEqual(CAMERA_NEAR_MAX);
    expect(clip.far).toBeGreaterThan(clip.near * 20);
    expect(clip.far).toBeLessThan(g.diagonal * 12);
    expect(LOGARITHMIC_DEPTH_BUFFER).toBe(false);
  });

  it("STEP 29.9 metric city (~84 km diagonal) scales the near cap and still tightens when zoomed in", () => {
    const metric: CityBounds = {
      minX: -41779,
      maxX: 31764,
      minZ: -38948,
      maxZ: 65809,
      minY: -16,
      maxY: 199,
    };
    const g = computeGlobalCityBounds([], metric);
    expect(g.diagonal).toBeGreaterThan(80_000);
    const overview = computeCameraClipRange(g);
    expect(overview.near).toBeGreaterThan(CAMERA_NEAR_MAX);
    expect(overview.near).toBeLessThan(g.diagonal * 0.01);
    expect(overview.far).toBeGreaterThan(g.diagonal);
    const street = computeAdaptiveCameraClip(g, 80);
    expect(street.near).toBeGreaterThanOrEqual(CAMERA_NEAR_MIN);
    expect(street.near).toBeLessThan(overview.near);
  });

  it("adaptive clip keeps a sane far/near ratio and does not use a tiny near", () => {
    const g = computeGlobalCityBounds([], ODESSA_BOUNDS);
    const overview = computeAdaptiveCameraClip(g, g.diagonal, 8000);
    const close = computeAdaptiveCameraClip(g, 40, 8000);
    expect(overview.near).toBeGreaterThanOrEqual(CAMERA_NEAR_MIN);
    expect(close.near).toBeGreaterThanOrEqual(CAMERA_NEAR_MIN);
    expect(close.near).toBeLessThanOrEqual(CAMERA_NEAR_MAX);
    expect(overview.far / overview.near).toBeLessThan(4000);
    expect(overview.far / overview.near).toBeGreaterThan(20);
    expect(LOGARITHMIC_DEPTH_BUFFER).toBe(false);
  });

  it("respects an optional far cap without collapsing the ratio", () => {
    const g = computeGlobalCityBounds([], ODESSA_BOUNDS);
    const clip = computeCameraClipRange(g, 8000);
    expect(clip.far).toBeLessThanOrEqual(8000);
    expect(clip.far / clip.near).toBeGreaterThan(20);
  });

  it("fitCameraToOdessa uses clip helper and restores overview target at city center", () => {
    const g = computeGlobalCityBounds([], ODESSA_BOUNDS);
    const cam = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 100);
    const fit = fitCameraToOdessaBounds(g, cam, 16 / 9);
    expect(fit.near).toBeGreaterThanOrEqual(CAMERA_NEAR_MIN);
    expect(fit.near).toBeLessThanOrEqual(CAMERA_NEAR_MAX);
    expect(fit.target.x).toBeCloseTo(g.center.x, 5);
    expect(fit.target.z).toBeCloseTo(g.center.z, 5);
    expect(fit.minDistance).toBeLessThan(fit.maxDistance);
    expect(fit.minDistance).toBeGreaterThanOrEqual(CAMERA_MIN_DISTANCE_M);
  });
});

describe("city camera polar / home / 2D", () => {
  it("keeps 3D polar above the horizon and never flips", () => {
    expect(CAMERA_POLAR_3D_MIN).toBeGreaterThan(0);
    expect(CAMERA_POLAR_3D_MAX).toBeLessThan(Math.PI / 2);
    expect(CAMERA_POLAR_3D_MAX).toBeGreaterThan(CAMERA_POLAR_3D_MIN);
    expect(polarLimitsForViewMode("3d").maxPolarAngle).toBe(CAMERA_POLAR_3D_MAX);
  });

  it("2D polar is near-nadir and still allows a slight tilt", () => {
    expect(CAMERA_POLAR_2D_MAX).toBeLessThan(0.35);
    expect(CAMERA_POLAR_2D_MIN).toBeGreaterThan(0);
    const lim = polarLimitsForViewMode("2d");
    expect(lim.maxPolarAngle).toBeLessThan(0.35);
    expect(lim.maxPolarAngle).toBeLessThan(CAMERA_POLAR_3D_MAX);
  });

  it("home tween is 0.8–1.5s and ground constraint lifts the camera", () => {
    expect(HOME_TWEEN_MS).toBeGreaterThanOrEqual(800);
    expect(HOME_TWEEN_MS).toBeLessThanOrEqual(1500);
    const camera = { position: { x: 0, y: -4, z: 10 } };
    const target = { x: 0, y: -2, z: 0 };
    const changed = applyCameraGroundConstraint(camera, target, 0, CAMERA_MIN_HEIGHT_ABOVE_BASE_M);
    expect(changed).toBe(true);
    expect(target.y).toBe(0);
    expect(camera.position.y).toBe(CAMERA_MIN_HEIGHT_ABOVE_BASE_M);
  });

  it("top-down pose looks at city center without remapping coordinates", () => {
    const g = computeGlobalCityBounds([], ODESSA_BOUNDS);
    const pose = topDownPose(g);
    expect(pose.target.x).toBeCloseTo(g.center.x, 5);
    expect(pose.target.z).toBeCloseTo(g.center.z, 5);
    expect(pose.position.y).toBeGreaterThan(g.center.y);
  });
});

describe("cityDebug query flag", () => {
  it("is off unless ?cityDebug=1", () => {
    expect(isCityDebugEnabled()).toBe(false);
  });
});

describe("Odessa distance-aware pan scaling", () => {
  const diagonal = 1280;

  it("keeps ~1.0x compensation at far / overview distance", () => {
    expect(distancePanCompensation(diagonal * 0.9, diagonal)).toBeCloseTo(1, 1);
  });

  it("boosts pan at district and block distances", () => {
    const far = distancePanCompensation(diagonal, diagonal);
    const medium = distancePanCompensation(diagonal * 0.5, diagonal);
    const near = distancePanCompensation(diagonal * 0.08, diagonal);
    expect(medium).toBeGreaterThan(far);
    expect(medium).toBeGreaterThanOrEqual(1.2);
    expect(medium).toBeLessThanOrEqual(1.6);
    expect(near).toBeGreaterThanOrEqual(2);
    expect(near).toBeLessThanOrEqual(4);
  });

  it("clamps very-near compensation so pan does not explode", () => {
    expect(distancePanCompensation(1, diagonal)).toBe(4);
    expect(distancePanCompensation(0, diagonal)).toBe(4);
    const speed = panSpeedForDistance({
      distance: 1,
      cityDiagonal: diagonal,
      viewportHeight: 640,
      basePanSpeed: BASE_PAN_SPEED,
    });
    expect(speed).toBeLessThanOrEqual(BASE_PAN_SPEED * 4 * 1.25);
    expect(speed).toBeGreaterThan(BASE_PAN_SPEED);
  });

  it("uses screen-space panning, damping, zoom-to-cursor; logarithmic depth stays off", () => {
    expect(CITY_SCREEN_SPACE_PANNING).toBe(true);
    expect(CITY_ZOOM_TOWARD_POINTER).toBe(true);
    expect(CAMERA_DAMPING_FACTOR).toBeGreaterThanOrEqual(0.07);
    expect(CAMERA_DAMPING_FACTOR).toBeLessThanOrEqual(0.12);
    expect(LOGARITHMIC_DEPTH_BUFFER).toBe(false);
  });
});
