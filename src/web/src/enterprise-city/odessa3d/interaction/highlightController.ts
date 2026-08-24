/**
 * Per-mesh material clone highlight. Never mutates interned/shared materials.
 */

import * as THREE from "three";
import type { PickableEntity } from "./types";

/** Cool steel tint — never a saturated green flood on the city. */
export const HOVER_HIGHLIGHT_HEX = 0x8aa4b8;
export const SELECT_HIGHLIGHT_HEX = 0x4d7284;

export const HOVER_EMISSIVE = 0.07;
export const SELECT_EMISSIVE = 0.16;
const EDGE_OPACITY_HOVER = 0.28;
const EDGE_OPACITY_SELECT = 0.42;

type Slot = {
  mesh: THREE.Mesh;
  original: THREE.Material | THREE.Material[];
  clones: THREE.Material[];
  mode: "hover" | "selected";
  edges: THREE.LineSegments | null;
};

function asList(mat: THREE.Material | THREE.Material[]): THREE.Material[] {
  return Array.isArray(mat) ? mat : [mat];
}

function parseCssHex(value: string, fallback: number): number {
  const v = value.trim();
  const m = /^#([0-9a-fA-F]{6})$/.exec(v);
  if (!m) return fallback;
  return parseInt(m[1], 16);
}

export function highlightHexFromTokens(): { hover: number; selected: number } {
  if (typeof document === "undefined") {
    return { hover: HOVER_HIGHLIGHT_HEX, selected: SELECT_HIGHLIGHT_HEX };
  }
  const styles = getComputedStyle(document.documentElement);
  const primary = parseCssHex(styles.getPropertyValue("--eds-primary"), SELECT_HIGHLIGHT_HEX);
  return { hover: HOVER_HIGHLIGHT_HEX, selected: primary || SELECT_HIGHLIGHT_HEX };
}

function tintMaterial(mat: THREE.Material, hex: number, intensity: number) {
  const anyMat = mat as THREE.MeshStandardMaterial;
  if ("emissive" in anyMat && anyMat.emissive) {
    anyMat.emissive.setHex(hex);
    anyMat.emissiveIntensity = intensity;
  } else if ("color" in anyMat && anyMat.color) {
    anyMat.color.lerp(new THREE.Color(hex), intensity * 0.35);
  }
  mat.needsUpdate = true;
}

function attachEdgeOverlay(mesh: THREE.Mesh, hex: number, opacity: number): THREE.LineSegments | null {
  const geo = mesh.geometry;
  if (!geo) return null;
  const pos = geo.getAttribute("position");
  if (pos && pos.count > 8000) return null;
  const edges = new THREE.EdgesGeometry(geo, 35);
  const line = new THREE.LineSegments(
    edges,
    new THREE.LineBasicMaterial({
      color: hex,
      transparent: true,
      opacity,
      depthTest: true,
      depthWrite: false,
    }),
  );
  line.name = "odessaHighlightEdges";
  line.userData.odessaHighlightHelper = true;
  line.raycast = () => undefined;
  mesh.add(line);
  return line;
}

function detachEdgeOverlay(line: THREE.LineSegments | null) {
  if (!line) return;
  line.parent?.remove(line);
  line.geometry?.dispose();
  const mat = line.material;
  if (mat && !Array.isArray(mat)) mat.dispose();
}

function cloneMaterials(source: THREE.Material | THREE.Material[]): THREE.Material[] {
  return asList(source).map((m) => {
    const clone = m.clone();
    clone.userData = { ...m.userData, odessaHighlightClone: true };
    return clone;
  });
}

function assignClones(mesh: THREE.Mesh, clones: THREE.Material[], original: THREE.Material | THREE.Material[]) {
  mesh.material = Array.isArray(original) ? clones : clones[0];
}

function disposeClones(clones: THREE.Material[]) {
  for (const c of clones) c.dispose();
}

export class HighlightController {
  private hover: Slot | null = null;
  private selected: Slot | null = null;
  private cloneCount = 0;
  private colors = highlightHexFromTokens();
  private boundsHelper: THREE.Box3Helper | null = null;
  private boundsGroup: THREE.Group | null = null;
  private showBounds = false;

  attachDebugGroup(group: THREE.Group) {
    this.boundsGroup = group;
  }

  setShowBounds(on: boolean) {
    this.showBounds = on;
    if (!on) this.clearBoundsHelper();
  }

  materialCloneCount(): number {
    return this.cloneCount;
  }

  setHover(mesh: THREE.Mesh | null) {
    if (this.hover?.mesh === mesh) return;
    this.releaseSlot("hover");
    if (!mesh) return;
    if (this.selected?.mesh === mesh) return;
    this.hover = this.apply(mesh, "hover");
  }

  setSelected(mesh: THREE.Mesh | null) {
    if (this.selected?.mesh === mesh) {
      this.syncBounds(mesh);
      return;
    }
    const wasHoverSame = this.hover?.mesh === mesh;
    this.releaseSlot("selected");
    if (wasHoverSame) this.releaseSlot("hover");
    if (!mesh) {
      this.clearBoundsHelper();
      return;
    }
    if (this.hover?.mesh === mesh) this.releaseSlot("hover");
    this.selected = this.apply(mesh, "selected");
    this.syncBounds(mesh);
  }

  applyIds(registryGet: (id: string) => THREE.Object3D | undefined, hoveredPickId: string | null, selectedPickId: string | null) {
    const sel = selectedPickId ? registryGet(selectedPickId) : undefined;
    const hov = hoveredPickId ? registryGet(hoveredPickId) : undefined;
    this.setSelected(sel && (sel as THREE.Mesh).isMesh ? (sel as THREE.Mesh) : null);
    if (hoveredPickId && hoveredPickId !== selectedPickId) {
      this.setHover(hov && (hov as THREE.Mesh).isMesh ? (hov as THREE.Mesh) : null);
    } else {
      this.setHover(null);
    }
  }

  releaseObject(obj: THREE.Object3D) {
    if (this.hover?.mesh === obj) this.releaseSlot("hover");
    if (this.selected?.mesh === obj) this.releaseSlot("selected");
  }

  releaseAsset(assetId: string, pickables: PickableEntity[]) {
    for (const p of pickables) {
      if (p.assetId !== assetId) continue;
      if (this.hover && this.hover.mesh.uuid === p.objectUuid) this.releaseSlot("hover");
      if (this.selected && this.selected.mesh.uuid === p.objectUuid) this.releaseSlot("selected");
    }
  }

  clearAll() {
    this.releaseSlot("hover");
    this.releaseSlot("selected");
    this.clearBoundsHelper();
  }

  private apply(mesh: THREE.Mesh, mode: "hover" | "selected"): Slot {
    const original = mesh.material;
    const clones = cloneMaterials(original);
    const hex = mode === "selected" ? this.colors.selected : this.colors.hover;
    const intensity = mode === "selected" ? SELECT_EMISSIVE : HOVER_EMISSIVE;
    for (const c of clones) tintMaterial(c, hex, intensity);
    assignClones(mesh, clones, original);
    const edges = attachEdgeOverlay(mesh, hex, mode === "selected" ? EDGE_OPACITY_SELECT : EDGE_OPACITY_HOVER);
    this.cloneCount += clones.length;
    return { mesh, original, clones, mode, edges };
  }

  private releaseSlot(which: "hover" | "selected") {
    const slot = which === "hover" ? this.hover : this.selected;
    if (!slot) return;
    slot.mesh.material = slot.original;
    detachEdgeOverlay(slot.edges);
    disposeClones(slot.clones);
    this.cloneCount = Math.max(0, this.cloneCount - slot.clones.length);
    if (which === "hover") this.hover = null;
    else this.selected = null;
  }

  private syncBounds(mesh: THREE.Mesh | null) {
    if (!this.showBounds || !mesh || !this.boundsGroup) {
      if (!this.showBounds) this.clearBoundsHelper();
      return;
    }
    this.clearBoundsHelper();
    const box = new THREE.Box3().setFromObject(mesh);
    const helper = new THREE.Box3Helper(box, this.colors.selected);
    helper.userData.odessaHighlightHelper = true;
    this.boundsGroup.add(helper);
    this.boundsHelper = helper;
  }

  private clearBoundsHelper() {
    if (!this.boundsHelper) return;
    this.boundsHelper.parent?.remove(this.boundsHelper);
    const line = this.boundsHelper as THREE.LineSegments;
    line.geometry?.dispose();
    const mat = line.material;
    if (mat && !Array.isArray(mat)) mat.dispose();
    this.boundsHelper = null;
  }
}
