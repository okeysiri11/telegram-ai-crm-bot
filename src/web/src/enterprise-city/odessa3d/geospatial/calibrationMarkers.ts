/**
 * Temporary A/B/C pins for the calibration session. Independent of GeoAnchor overlays.
 * Not pickable. Does not mutate city materials.
 */

import * as THREE from "three";
import type { CalibrationSlotId, LocalWorldCoordinate } from "./types";

const COLORS: Record<string, number> = {
  A: 0x3ecfad,
  B: 0xc9a227,
  C: 0x6b8cff,
  CHECK: 0xe8e8e8,
};

export type CalibrationMarkerId = CalibrationSlotId | "CHECK";

export type CalibrationMarkerPoint = {
  id: CalibrationMarkerId;
  world: LocalWorldCoordinate;
};

function letterTexture(letter: string, hex: number): THREE.CanvasTexture | null {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    ctx.clearRect(0, 0, 64, 64);
    ctx.beginPath();
    ctx.arc(32, 32, 28, 0, Math.PI * 2);
    ctx.fillStyle = `#${hex.toString(16).padStart(6, "0")}`;
    ctx.fill();
    ctx.fillStyle = "#0b1118";
    ctx.font = "bold 32px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(letter, 32, 34);
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}

export class CalibrationMarkerRenderer {
  readonly group = new THREE.Group();
  private nodes: THREE.Object3D[] = [];

  constructor() {
    this.group.name = "calibration_markers";
    this.group.visible = false;
  }

  sync(points: readonly CalibrationMarkerPoint[], visible: boolean) {
    this.clearMeshes();
    this.group.visible = visible && points.length > 0;
    if (!this.group.visible) return;
    for (const p of points) {
      const node = this.makePin(p.id === "CHECK" ? "✓" : p.id, COLORS[p.id] ?? 0xe8e8e8);
      node.position.set(p.world.x, p.world.y + 2.2, p.world.z);
      node.userData.calibrationSlot = p.id;
      node.userData.odessaHighlightHelper = true;
      this.group.add(node);
      this.nodes.push(node);
    }
  }

  updateScales(camera: THREE.Camera) {
    if (!this.group.visible) return;
    for (const node of this.nodes) {
      const dist = camera.position.distanceTo(node.position);
      const s = Math.min(8, Math.max(1.1, dist * 0.012));
      node.scale.setScalar(s);
    }
  }

  dispose() {
    this.clearMeshes();
  }

  private makePin(letter: string, hex: number): THREE.Group {
    const root = new THREE.Group();
    const disc = new THREE.Mesh(
      new THREE.CircleGeometry(0.85, 20),
      new THREE.MeshBasicMaterial({ color: hex, depthTest: true, transparent: true, opacity: 0.88 }),
    );
    disc.rotation.x = -Math.PI / 2;
    disc.userData.odessaHighlightHelper = true;
    disc.raycast = () => undefined;
    const map = letterTexture(letter, hex);
    const sprite = new THREE.Sprite(
      new THREE.SpriteMaterial({ map: map ?? undefined, color: hex, depthTest: true, transparent: true }),
    );
    sprite.position.y = 1.6;
    sprite.scale.set(2.2, 2.2, 1);
    sprite.userData.odessaHighlightHelper = true;
    sprite.raycast = () => undefined;
    root.add(disc, sprite);
    root.userData.odessaHighlightHelper = true;
    return root;
  }

  private clearMeshes() {
    for (const node of this.nodes) {
      node.parent?.remove(node);
      node.traverse((obj) => {
        const mesh = obj as THREE.Mesh | THREE.Sprite;
        if ("geometry" in mesh && mesh.geometry) mesh.geometry.dispose();
        const mat = (mesh as THREE.Mesh).material;
        if (mat && !Array.isArray(mat)) {
          if ("map" in mat && mat.map) mat.map.dispose();
          mat.dispose();
        }
      });
    }
    this.nodes = [];
  }
}
