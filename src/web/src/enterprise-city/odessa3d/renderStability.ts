/**
 * STEP 29.2 — Odessa render stability (depth, color space, isolation diagnostics).
 * Does not move city geometry or touch georeference/calibration.
 */

import * as THREE from "three";

export const COLOR_TEXTURE_KEYS = ["map", "emissiveMap", "envMap"] as const;
export const DATA_TEXTURE_KEYS = [
  "normalMap",
  "roughnessMap",
  "metalnessMap",
  "aoMap",
  "bumpMap",
  "displacementMap",
  "alphaMap",
  "lightMap",
] as const;

export type RenderIsolationState = {
  baseModelOnly: boolean;
  disableWater: boolean;
  disableOverlays: boolean;
  neutralMaterial: boolean;
};

export const DEFAULT_RENDER_ISOLATION: RenderIsolationState = {
  baseModelOnly: false,
  disableWater: false,
  disableOverlays: false,
  neutralMaterial: false,
};

export type RenderStabilityStats = {
  cityRootInstances: number;
  meshCount: number;
  visibleMeshes: number;
  transparentMaterials: number;
  depthWriteFalseCount: number;
  cameraNear: number;
  cameraFar: number;
  farNearRatio: number;
  rendererPixelRatio: number;
  drawCalls: number;
  triangles: number;
};

const COLOR_SPACE_MARK = "odessaColorSpaceFixed";

export function applyTextureColorSpace(tex: THREE.Texture, kind: "color" | "data"): boolean {
  const wanted = kind === "color" ? THREE.SRGBColorSpace : THREE.LinearSRGBColorSpace;
  if (tex.colorSpace === wanted) return false;
  tex.colorSpace = wanted;
  tex.needsUpdate = true;
  return true;
}

/** sRGB for color maps only. Data maps stay linear — sRGB normals/roughness cause angle-dependent washout. */
export function applyMaterialTextureColorSpaces(mat: THREE.Material): boolean {
  const ud = mat.userData as { [COLOR_SPACE_MARK]?: boolean };
  if (ud[COLOR_SPACE_MARK]) return false;
  let changed = false;
  const rec = mat as unknown as Record<string, unknown>;
  for (const key of COLOR_TEXTURE_KEYS) {
    const tex = rec[key];
    if (tex instanceof THREE.Texture) changed = applyTextureColorSpace(tex, "color") || changed;
  }
  for (const key of DATA_TEXTURE_KEYS) {
    const tex = rec[key];
    if (tex instanceof THREE.Texture) changed = applyTextureColorSpace(tex, "data") || changed;
  }
  ud[COLOR_SPACE_MARK] = true;
  if (changed) mat.needsUpdate = true;
  return changed;
}

export function applyRootTextureColorSpaces(root: THREE.Object3D): number {
  const seen = new Set<THREE.Material>();
  let n = 0;
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const mat of mats) {
      if (!mat || seen.has(mat)) continue;
      seen.add(mat);
      if (applyMaterialTextureColorSpaces(mat)) n += 1;
    }
  });
  return n;
}

export function countNamedObject(scene: THREE.Object3D, name: string): number {
  let n = 0;
  scene.traverse((obj) => {
    if (obj.name === name) n += 1;
  });
  return n;
}

export function collectRenderStabilityStats(input: {
  scene: THREE.Object3D;
  cityRoot: THREE.Object3D;
  camera: THREE.PerspectiveCamera | null;
  renderer: THREE.WebGLRenderer | null;
  cityRootName?: string;
}): RenderStabilityStats {
  let meshCount = 0;
  let visibleMeshes = 0;
  let transparentMaterials = 0;
  let depthWriteFalseCount = 0;
  const seen = new Set<THREE.Material>();
  input.cityRoot.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    meshCount += 1;
    if (mesh.visible) visibleMeshes += 1;
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const mat of mats) {
      if (!mat || seen.has(mat)) continue;
      seen.add(mat);
      if (mat.transparent) transparentMaterials += 1;
      if (mat.depthWrite === false) depthWriteFalseCount += 1;
    }
  });
  const near = input.camera?.near ?? 0;
  const far = input.camera?.far ?? 0;
  const info = input.renderer?.info.render;
  return {
    cityRootInstances: countNamedObject(input.scene, input.cityRootName ?? "odessaCityRoot"),
    meshCount,
    visibleMeshes,
    transparentMaterials,
    depthWriteFalseCount,
    cameraNear: near,
    cameraFar: far,
    farNearRatio: near > 0 ? far / near : 0,
    rendererPixelRatio: input.renderer?.getPixelRatio() ?? 1,
    drawCalls: info?.calls ?? 0,
    triangles: info?.triangles ?? 0,
  };
}

const ISO_VIS = "odessaIsoVisible";

export function setSubtreeIsolatedHidden(root: THREE.Object3D | null | undefined, hidden: boolean) {
  if (!root) return;
  const ud = root.userData as { [ISO_VIS]?: boolean };
  if (hidden) {
    if (ud[ISO_VIS] === undefined) ud[ISO_VIS] = root.visible;
    root.visible = false;
  } else if (ud[ISO_VIS] !== undefined) {
    root.visible = ud[ISO_VIS];
    delete ud[ISO_VIS];
  }
}

export function hideWaterLikeMeshes(root: THREE.Object3D, hidden: boolean, isWater: (mesh: THREE.Mesh) => boolean) {
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh || !isWater(mesh)) return;
    const ud = mesh.userData as { [ISO_VIS]?: boolean };
    if (hidden) {
      if (ud[ISO_VIS] === undefined) ud[ISO_VIS] = mesh.visible;
      mesh.visible = false;
    } else if (ud[ISO_VIS] !== undefined) {
      mesh.visible = ud[ISO_VIS];
      delete ud[ISO_VIS];
    }
  });
}

const ORIG_MAT = "odessaIsoMaterial";

export function applyNeutralMaterialDiagnostic(
  root: THREE.Object3D,
  on: boolean,
  shared: THREE.Material,
) {
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    const ud = mesh.userData as { [ORIG_MAT]?: THREE.Material | THREE.Material[] };
    if (on) {
      if (ud[ORIG_MAT] === undefined) ud[ORIG_MAT] = mesh.material;
      mesh.material = shared;
    } else if (ud[ORIG_MAT] !== undefined) {
      mesh.material = ud[ORIG_MAT];
      delete ud[ORIG_MAT];
    }
  });
}

export function createNeutralDiagnosticMaterial(): THREE.MeshLambertMaterial {
  const mat = new THREE.MeshLambertMaterial({
    color: 0x9aa3ad,
    side: THREE.FrontSide,
    depthWrite: true,
    depthTest: true,
    transparent: false,
  });
  mat.name = "odessaNeutralDiagnostic";
  return mat;
}

export type LightingColorAudit = {
  emissiveActiveMaterials: number;
  metalTexturedMaterials: number;
  srgbDataMapViolations: number;
  vertexColorMeshes: number;
  transparentTexturedMaterials: number;
};

const TONE_MAPPING_NAMES: Record<number, string> = {
  [THREE.NoToneMapping]: "NoToneMapping",
  [THREE.LinearToneMapping]: "LinearToneMapping",
  [THREE.ReinhardToneMapping]: "ReinhardToneMapping",
  [THREE.CineonToneMapping]: "CineonToneMapping",
  [THREE.ACESFilmicToneMapping]: "ACESFilmicToneMapping",
  [THREE.AgXToneMapping]: "AgXToneMapping",
  [THREE.NeutralToneMapping]: "NeutralToneMapping",
};

export function toneMappingName(toneMapping: number): string {
  return TONE_MAPPING_NAMES[toneMapping] ?? `unknown(${toneMapping})`;
}

/** FogExp2 mix estimate at a depth — how much of the pixel is fog color. */
export function fogMixAtDepth(density: number, depth: number): number {
  if (density <= 0 || depth <= 0) return 0;
  return 1 - Math.exp(-((density * depth) ** 2));
}

/**
 * One-shot washout audit: flags materials that can cause angle-dependent
 * brightening (active emissive, metal without metalnessMap, sRGB data maps).
 */
export function collectLightingColorAudit(cityRoot: THREE.Object3D): LightingColorAudit {
  const audit: LightingColorAudit = {
    emissiveActiveMaterials: 0,
    metalTexturedMaterials: 0,
    srgbDataMapViolations: 0,
    vertexColorMeshes: 0,
    transparentTexturedMaterials: 0,
  };
  const seen = new Set<THREE.Material>();
  cityRoot.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    if (mesh.geometry?.attributes.color) audit.vertexColorMeshes += 1;
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const mat of mats) {
      if (!mat || seen.has(mat)) continue;
      seen.add(mat);
      const std = mat as THREE.MeshStandardMaterial;
      if (std.isMeshStandardMaterial) {
        const emissiveOn =
          !!std.emissive && std.emissive.getHex() !== 0 && (std.emissiveIntensity ?? 1) > 0.01;
        if (emissiveOn || std.emissiveMap) audit.emissiveActiveMaterials += 1;
        if (std.map && !std.metalnessMap && (std.metalness ?? 0) > 0.5) {
          audit.metalTexturedMaterials += 1;
        }
        if (std.map && std.transparent) audit.transparentTexturedMaterials += 1;
      }
      const rec = mat as unknown as Record<string, unknown>;
      for (const key of DATA_TEXTURE_KEYS) {
        const tex = rec[key];
        if (tex instanceof THREE.Texture && tex.colorSpace === THREE.SRGBColorSpace) {
          audit.srgbDataMapViolations += 1;
        }
      }
    }
  });
  return audit;
}

/** Safari/Intel: skip stencil so the GPU can keep a 24-bit depth buffer. */
export function safariStableRendererOptions(antialias: boolean): THREE.WebGLRendererParameters {
  return {
    antialias,
    alpha: false,
    depth: true,
    stencil: false,
    powerPreference: "high-performance",
    logarithmicDepthBuffer: false,
    preserveDrawingBuffer: false,
  };
}
