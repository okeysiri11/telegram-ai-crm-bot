/**
 * Runtime sea appearance for canonical WEB_water only.
 * Does not restore WEB_bay, does not retarget rivers/lakes, does not edit GLBs.
 */

import * as THREE from "three";
import type { EnvironmentPreset, EnvironmentQuality } from "./environmentPresets";

const CANONICAL_SEA = /web_water/i;

export function isCanonicalSeaMesh(mesh: THREE.Mesh): boolean {
  if (!mesh?.isMesh) return false;
  return CANONICAL_SEA.test(mesh.name || "") || CANONICAL_SEA.test(mesh.parent?.name || "");
}

export function waterRoughnessForDistance(
  _distanceM: number,
  preset: EnvironmentPreset,
  quality: EnvironmentQuality,
): number {
  /** Frozen far roughness — camera orbit must not retint the sea. */
  if (quality === "low") return Math.max(preset.waterRoughnessFar, 0.72);
  return Math.max(preset.waterRoughnessFar, quality === "high" ? 0.72 : 0.74);
}

function materialsOf(mesh: THREE.Mesh): THREE.Material[] {
  return (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).filter(Boolean);
}

/** Tint + roughness on the existing standard material. Never assigns envMap. */
export function applyCanonicalSeaAppearance(
  mesh: THREE.Mesh,
  preset: EnvironmentPreset,
  distanceM = 600,
  quality: EnvironmentQuality = "medium",
): boolean {
  if (!isCanonicalSeaMesh(mesh) || !mesh.visible) return false;
  let applied = false;
  const roughness = waterRoughnessForDistance(distanceM, preset, quality);
  for (const mat of materialsOf(mesh)) {
    const std = mat as THREE.MeshStandardMaterial;
    if (!std.isMeshStandardMaterial) continue;
    std.color.setHex(preset.waterColor);
    std.metalness = 0;
    std.roughness = roughness;
    std.envMap = null;
    std.envMapIntensity = 0;
    std.transparent = false;
    std.opacity = 1;
    std.emissive?.setHex(0x000000);
    std.userData.odessaSeaOverride = true;
    std.needsUpdate = true;
    applied = true;
  }
  return applied;
}

export function collectCanonicalSeaMeshes(roots: Iterable<THREE.Object3D>): THREE.Mesh[] {
  const out: THREE.Mesh[] = [];
  for (const root of roots) {
    root.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (mesh.isMesh && isCanonicalSeaMesh(mesh) && mesh.visible) out.push(mesh);
    });
  }
  return out;
}

export function updateSeaDistanceResponse(
  meshes: readonly THREE.Mesh[],
  distanceM: number,
  preset: EnvironmentPreset,
  quality: EnvironmentQuality,
) {
  if (meshes.length === 0) return;
  const roughness = waterRoughnessForDistance(distanceM, preset, quality);
  for (const mesh of meshes) {
    const mats = materialsOf(mesh);
    for (const mat of mats) {
      const std = mat as THREE.MeshStandardMaterial;
      if (!std.isMeshStandardMaterial || !std.userData.odessaSeaOverride) continue;
      if (Math.abs(std.roughness - roughness) < 0.012) continue;
      std.roughness = roughness;
    }
  }
}
