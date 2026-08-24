/**
 * Developer-only local metric grid. Default OFF. Hidden unless calibration is READY.
 */

import * as THREE from "three";
import type { GeoCalibration } from "./types";
import { localMetersToWorld } from "./worldTransform";

export class GeoDebugGrid {
  readonly group = new THREE.Group();
  private helper: THREE.LineSegments | null = null;
  private enabled = false;

  constructor() {
    this.group.name = "geo_debug_grid";
    this.group.visible = false;
  }

  setEnabled(on: boolean) {
    this.enabled = on;
    this.group.visible = on && !!this.helper;
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  rebuild(calibration: GeoCalibration | null, spacingMeters: 100 | 500 = 100, extentMeters = 1200) {
    this.clear();
    if (!calibration || !this.enabled) {
      this.group.visible = false;
      return;
    }
    const half = Math.max(extentMeters, spacingMeters * 2);
    const points: THREE.Vector3[] = [];
    for (let e = -half; e <= half; e += spacingMeters) {
      const a = localMetersToWorld({ east: e, north: -half, up: 0.4 }, calibration);
      const b = localMetersToWorld({ east: e, north: half, up: 0.4 }, calibration);
      points.push(new THREE.Vector3(a.x, a.y, a.z), new THREE.Vector3(b.x, b.y, b.z));
    }
    for (let n = -half; n <= half; n += spacingMeters) {
      const a = localMetersToWorld({ east: -half, north: n, up: 0.4 }, calibration);
      const b = localMetersToWorld({ east: half, north: n, up: 0.4 }, calibration);
      points.push(new THREE.Vector3(a.x, a.y, a.z), new THREE.Vector3(b.x, b.y, b.z));
    }
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    const mat = new THREE.LineBasicMaterial({
      color: 0x3ecfad,
      transparent: true,
      opacity: 0.28,
      depthWrite: false,
    });
    this.helper = new THREE.LineSegments(geo, mat);
    this.helper.userData.odessaHighlightHelper = true;
    this.group.add(this.helper);
    this.group.visible = true;
  }

  dispose() {
    this.clear();
  }

  private clear() {
    if (!this.helper) return;
    this.helper.parent?.remove(this.helper);
    this.helper.geometry.dispose();
    const mat = this.helper.material;
    if (!Array.isArray(mat)) mat.dispose();
    this.helper = null;
  }
}

export function gridSpacingForDistance(distanceWorld: number, metersPerWorldUnit: number): 100 | 500 {
  const meters = distanceWorld * metersPerWorldUnit;
  return meters > 700 ? 500 : 100;
}
