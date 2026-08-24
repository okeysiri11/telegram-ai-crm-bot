/**
 * Lightweight 3D markers for GeoAnchors. Data stays in geoAnchors; this only draws.
 * Small counts only. World positions are cached; scale follows camera distance.
 */

import * as THREE from "three";
import type { CachedAnchor } from "./geoAnchors";
import type { BoundsClass } from "./types";

const COLOR_ENTERPRISE = 0x0f6a5a;
const COLOR_POI = 0x8a93a3;
const COLOR_VEHICLE = 0xc9a227;
const COLOR_SELECTED = 0x3ecfad;
const COLOR_OUT = 0x994444;

function colorFor(type: string, selected: boolean, bounds: BoundsClass | null): number {
  if (selected) return COLOR_SELECTED;
  if (bounds === "OUT_OF_BOUNDS") return COLOR_OUT;
  if (type === "enterprise") return COLOR_ENTERPRISE;
  if (type === "vehicle" || type === "drone") return COLOR_VEHICLE;
  return COLOR_POI;
}

export class GeoAnchorRenderer {
  readonly group = new THREE.Group();
  private meshes: THREE.Mesh[] = [];
  private visualOffset = 2.4;

  constructor() {
    this.group.name = "geo_anchors";
    this.group.visible = false;
  }

  setVisualOffset(worldUnits: number) {
    this.visualOffset = worldUnits;
  }

  sync(
    cached: CachedAnchor[],
    opts: {
      enabled: boolean;
      selectedEntityId?: string | null;
      classify?: (id: string) => BoundsClass | null;
    },
  ) {
    this.clearMeshes();
    this.group.visible = opts.enabled;
    if (!opts.enabled) return;
    for (const row of cached) {
      if (!row.world) continue;
      const bounds = opts.classify?.(row.anchor.id) ?? null;
      if (bounds === "OUT_OF_BOUNDS") continue;
      const selected = !!opts.selectedEntityId && row.anchor.entityId === opts.selectedEntityId;
      const mesh = this.makePin(colorFor(row.anchor.type, selected, bounds));
      mesh.position.set(row.world.x, row.world.y + this.visualOffset, row.world.z);
      mesh.userData.geoAnchorId = row.anchor.id;
      mesh.userData.entityId = row.anchor.entityId;
      mesh.userData.odessaHighlightHelper = true;
      this.group.add(mesh);
      this.meshes.push(mesh);
    }
  }

  updateScales(camera: THREE.Camera) {
    if (!this.group.visible) return;
    for (const mesh of this.meshes) {
      const dist = camera.position.distanceTo(mesh.position);
      const s = Math.min(8, Math.max(1.1, dist * 0.012));
      mesh.scale.setScalar(s);
    }
  }

  pickEntityId(object: THREE.Object3D | null | undefined): string | null {
    let node: THREE.Object3D | null = object ?? null;
    while (node) {
      if (typeof node.userData?.entityId === "string") return node.userData.entityId;
      node = node.parent;
    }
    return null;
  }

  dispose() {
    this.clearMeshes();
  }

  private makePin(hex: number): THREE.Mesh {
    const geo = new THREE.ConeGeometry(0.55, 2.2, 6);
    const mat = new THREE.MeshBasicMaterial({ color: hex, depthTest: true, transparent: true, opacity: 0.92 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.x = Math.PI;
    return mesh;
  }

  private clearMeshes() {
    for (const mesh of this.meshes) {
      mesh.parent?.remove(mesh);
      mesh.geometry.dispose();
      const mat = mesh.material;
      if (!Array.isArray(mat)) mat.dispose();
    }
    this.meshes = [];
  }
}
