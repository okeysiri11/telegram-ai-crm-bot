/**
 * One-time untextured urban visual pass — classify, normalize, vary buildings.
 * Cached on materials via userData. Never runs in the render loop.
 */

import * as THREE from "three";
import { nameLooksLikeWater } from "../waterSurfaceGuard";
import {
  classifyUrbanMaterial,
  isPlaceholderUrban,
  type UrbanMaterialClass,
} from "./materialClassify";
import type { EnvironmentQuality } from "./environmentPresets";

export type VisualPrepStats = {
  classifiedMaterials: Record<UrbanMaterialClass, number>;
  normalizedMaterials: number;
  texturedMaterialsSkipped: number;
  buildingVariationCount: number;
};

export function emptyVisualPrepStats(): VisualPrepStats {
  return {
    classifiedMaterials: {
      BUILDING: 0,
      ROAD: 0,
      GROUND: 0,
      VEGETATION: 0,
      WATER: 0,
      INDUSTRIAL: 0,
      UNKNOWN: 0,
    },
    normalizedMaterials: 0,
    texturedMaterialsSkipped: 0,
    buildingVariationCount: 0,
  };
}

export function mergeVisualPrepStats(into: VisualPrepStats, add: VisualPrepStats) {
  for (const key of Object.keys(add.classifiedMaterials) as UrbanMaterialClass[]) {
    into.classifiedMaterials[key] += add.classifiedMaterials[key];
  }
  into.normalizedMaterials += add.normalizedMaterials;
  into.texturedMaterialsSkipped += add.texturedMaterialsSkipped;
  into.buildingVariationCount += add.buildingVariationCount;
}

export function formatClassifiedMaterials(stats: VisualPrepStats): string {
  return (Object.entries(stats.classifiedMaterials) as [UrbanMaterialClass, number][])
    .filter(([, n]) => n > 0)
    .map(([k, n]) => `${k}:${n}`)
    .join(" ") || "none";
}

/** FNV-1a → 0..1, stable across sessions. */
export function stableUnitHash(seed: string): number {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) / 4294967295;
}

/** Deterministic brightness variation in ±3–6%. */
export function buildingVariationDelta(assetId: string, materialName: string): number {
  const u = stableUnitHash(`${assetId}|${materialName}`);
  const amplitude = 0.03 + u * 0.03;
  return (u - 0.5) * 2 * amplitude;
}

function hslOf(color: THREE.Color): { h: number; s: number; l: number } {
  const hsl = { h: 0, s: 0, l: 0 };
  color.getHSL(hsl);
  return hsl;
}

function isTextured(std: THREE.MeshStandardMaterial): boolean {
  return !!(std.map || std.emissiveMap || std.normalMap || std.roughnessMap || std.metalnessMap);
}

export type UrbanVisualContext = {
  assetId: string;
  meshName: string;
  quality: EnvironmentQuality;
  mesh?: THREE.Mesh;
};

export type UrbanVisualResult = {
  classified: UrbanMaterialClass;
  normalized: boolean;
  varied: boolean;
  skippedTextured: boolean;
};

/**
 * MEDIUM/HIGH readability for untextured placeholder urban materials.
 * LOW classifies only. Textured and water materials are never rewritten.
 */
export function applyUrbanVisualPass(
  mat: THREE.Material,
  ctx: UrbanVisualContext,
): UrbanVisualResult {
  const std = mat as THREE.MeshStandardMaterial;
  const empty: UrbanVisualResult = {
    classified: "UNKNOWN",
    normalized: false,
    varied: false,
    skippedTextured: false,
  };
  if (!std.isMeshStandardMaterial) return empty;
  if (std.userData.odessaVisualTuned) {
    return {
      classified: (std.userData.odessaMaterialClass as UrbanMaterialClass) || "UNKNOWN",
      normalized: !!std.userData.odessaNormalized,
      varied: !!std.userData.odessaVaried,
      skippedTextured: false,
    };
  }

  const name = std.name || "";
  if (nameLooksLikeWater(name) || std.userData.odessaSeaOverride) {
    std.userData.odessaMaterialClass = "WATER";
    std.userData.odessaVisualTuned = true;
    return { classified: "WATER", normalized: false, varied: false, skippedTextured: false };
  }
  if (isTextured(std) || !std.color) {
    std.userData.odessaVisualTuned = true;
    return { classified: "UNKNOWN", normalized: false, varied: false, skippedTextured: true };
  }

  const hsl = hslOf(std.color);
  const classified = classifyUrbanMaterial({
    meshName: ctx.meshName,
    materialName: name,
    assetId: ctx.assetId,
    saturation: hsl.s,
    lightness: hsl.l,
    hue: hsl.h,
  });
  std.userData.odessaMaterialClass = classified;

  if (ctx.quality === "low") {
    std.userData.odessaVisualTuned = true;
    return { classified, normalized: false, varied: false, skippedTextured: false };
  }

  if (classified === "WATER") {
    std.userData.odessaVisualTuned = true;
    return { classified, normalized: false, varied: false, skippedTextured: false };
  }

  let normalized = false;
  let varied = false;
  const placeholder = isPlaceholderUrban(hsl.s, hsl.l);

  if (classified === "VEGETATION") {
    if ((std.metalness ?? 0) > 0.02) {
      std.metalness = 0;
      normalized = true;
    }
    if ((std.roughness ?? 1) < 0.55) {
      std.roughness = 0.68;
      normalized = true;
    }
  } else if (classified === "ROAD" || classified === "GROUND") {
    std.metalness = 0;
    std.roughness = THREE.MathUtils.clamp(Math.max(std.roughness ?? 0.7, 0.7), 0.55, 0.85);
    if (classified === "ROAD") {
      std.color.multiplyScalar(0.9);
    }
    normalized = true;
  } else if (placeholder && (classified === "BUILDING" || classified === "INDUSTRIAL" || classified === "UNKNOWN")) {
    std.metalness = 0;
    std.roughness = THREE.MathUtils.clamp(std.roughness ?? 0.65, 0.55, 0.85);
    if (hsl.l > 0.86) {
      std.color.multiplyScalar(0.94);
    }
    if (std.emissive && std.emissive.getHex() !== 0 && (std.emissiveIntensity ?? 0) < 0.08) {
      std.emissive.setHex(0x000000);
    }
    normalized = true;
    if (classified === "BUILDING" && ctx.quality !== "low") {
      const delta = buildingVariationDelta(ctx.assetId, name || "mat");
      std.color.multiplyScalar(1 + delta);
      varied = true;
    }
    if (ctx.quality === "high" && classified === "BUILDING" && ctx.mesh) {
      const down = sampleDownwardRatio(ctx.mesh);
      if (down > 0.4) std.color.multiplyScalar(0.94);
    }
  }

  std.userData.odessaNormalized = normalized;
  std.userData.odessaVaried = varied;
  std.userData.odessaVisualTuned = true;
  if (normalized || varied) std.needsUpdate = true;
  return { classified, normalized, varied, skippedTextured: false };
}

/** Sample a few normals once — HIGH contact-shadow substitute, not SSAO. */
export function sampleDownwardRatio(mesh: THREE.Mesh, samples = 48): number {
  const attr = mesh.geometry?.getAttribute("normal");
  if (!attr || attr.count < 3) return 0;
  const step = Math.max(1, Math.floor(attr.count / samples));
  let down = 0;
  let n = 0;
  for (let i = 0; i < attr.count && n < samples; i += step) {
    if (attr.getY(i) < -0.35) down += 1;
    n += 1;
  }
  return n ? down / n : 0;
}

/** Backward-compatible white-plaster helper used by older tests. */
export function applyUntexturedReadability(mat: THREE.Material): boolean {
  const result = applyUrbanVisualPass(mat, {
    assetId: "compat",
    meshName: "",
    quality: "medium",
  });
  return result.normalized;
}
