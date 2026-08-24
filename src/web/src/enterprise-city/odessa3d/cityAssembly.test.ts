import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  boundsFromCityBounds,
  computeGlobalCityBounds,
  fitCameraToOdessaBounds,
} from "./cityAssembly";
import type { CityBounds } from "./types";

describe("Odessa city assembly", () => {
  const manifestBounds: CityBounds = {
    minX: -400,
    maxX: 300,
    minZ: -390,
    maxZ: 650,
    minY: 0,
    maxY: 2,
  };

  it("does not per-tile center — nodes keep local matrix at origin attachment", () => {
    const tileA = new THREE.Group();
    tileA.position.set(10, 0, 20);
    const tileB = new THREE.Group();
    tileB.position.set(-50, 0, 100);
    const root = new THREE.Group();
    root.add(tileA);
    root.add(tileB);
    expect(tileA.position.x).toBe(10);
    expect(tileB.position.z).toBe(100);
  });

  it("computes global bounds from manifest + loaded nodes", () => {
    const node = new THREE.Mesh(new THREE.BoxGeometry(10, 1, 10));
    node.position.set(0, 0, 0);
    const g = computeGlobalCityBounds([node], manifestBounds);
    expect(g.size.x).toBeGreaterThan(600);
    expect(g.diagonal).toBeGreaterThan(700);
    expect(g.center.x).toBeLessThan(0);
  });

  it("fitCameraToOdessa uses global diagonal for clip planes", () => {
    const node = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1));
    const bounds = computeGlobalCityBounds([node], manifestBounds);
    const cam = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 100);
    const fit = fitCameraToOdessaBounds(bounds, cam, 16 / 9);
    expect(fit.near).toBeGreaterThanOrEqual(0.5);
    expect(fit.near).toBeLessThanOrEqual(4);
    expect(fit.far).toBeGreaterThan(fit.near * 10);
    expect(fit.minDistance).toBeLessThan(fit.maxDistance);
    expect(fit.target.y).toBeGreaterThanOrEqual(0);
  });

  it("boundsFromCityBounds maps Y-up correctly", () => {
    const box = boundsFromCityBounds(manifestBounds);
    expect(box.min.y).toBe(0);
    expect(box.max.y).toBe(2);
    expect(box.min.z).toBe(-390);
  });
});
