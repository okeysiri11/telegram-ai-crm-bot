/**
 * Single-pass scene preparation after GLTF parse, before attach.
 * Visual classification/normalization is once-per-material, not per frame.
 */

import * as THREE from "three";
import { prepareMeshForPerformance } from "./odessaPerformance";
import {
  applyUrbanVisualPass,
  emptyVisualPrepStats,
  type VisualPrepStats,
} from "./environment/buildingReadability";
import type { EnvironmentQuality } from "./environment/environmentPresets";
import { applyMaterialTextureColorSpaces } from "./renderStability";
import { applyGroundDecalLayering, type DecalLayeringResult } from "./renderDebugTools";
import {
  ODESSA_VERTICAL_RECOVERY_MODE,
  applyOdessaVerticalScaleRecovery,
  type VerticalRecoveryResult,
} from "./verticalRecovery";
import {
  applySceneComponentRepair,
  emptySceneComponentRepairResult,
  type SceneComponentRepairResult,
} from "./componentRepair";
import { activeOdessaPackage } from "./odessaPackage";

export type PreparedSceneInfo = {
  root: THREE.Object3D;
  meshCount: number;
  materialCount: number;
  triangleCount: number;
  objectCount: number;
  visual: VisualPrepStats;
  decalLayering: DecalLayeringResult;
  verticalRecovery: VerticalRecoveryResult;
  componentRepair: SceneComponentRepairResult;
};

export function prepareParsedScene(
  root: THREE.Object3D,
  opts: {
    enableShadows: boolean;
    maxAnisotropy: number;
    assetId?: string;
    environmentQuality?: EnvironmentQuality;
  },
): PreparedSceneInfo {
  let meshCount = 0;
  let triangleCount = 0;
  let objectCount = 0;
  const seenMats = new Set<THREE.Material>();
  const visual = emptyVisualPrepStats();
  const quality = opts.environmentQuality ?? "medium";
  const assetId = opts.assetId || root.name || "asset";

  root.traverse((obj) => {
    objectCount += 1;
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    meshCount += 1;
    prepareMeshForPerformance(mesh, opts);
    const geo = mesh.geometry;
    if (geo?.index) triangleCount += geo.index.count / 3;
    else if (geo?.attributes.position) triangleCount += geo.attributes.position.count / 3;
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const mat of mats) {
      if (!mat) continue;
      const first = !seenMats.has(mat);
      seenMats.add(mat);
      const std = mat as THREE.MeshStandardMaterial;
      applyMaterialTextureColorSpaces(mat);
      if (std.isMeshStandardMaterial && !std.map && !std.color) {
        std.color = new THREE.Color(0x9aa3ad);
      }
      if (!first || !std.isMeshStandardMaterial) continue;
      const result = applyUrbanVisualPass(std, {
        assetId,
        meshName: mesh.name || root.name || "",
        quality,
        mesh,
      });
      visual.classifiedMaterials[result.classified] += 1;
      if (result.normalized) visual.normalizedMaterials += 1;
      if (result.varied) visual.buildingVariationCount += 1;
      if (result.skippedTextured) visual.texturedMaterialsSkipped += 1;
    }
  });

  /* STEP 29.9: the REBUILT_METRIC package (default) is authored at
   * 1 unit = 1 meter — the vendor geometry rendered directly, no runtime
   * geometry recovery of any kind. The STEP 29.5–29.8 recovery chain below
   * exists only for the legacy CURRENT_BROKEN rollback package. */
  const pkg = activeOdessaPackage();
  const recoveryMode = pkg.runtimeGeometryRecovery ? ODESSA_VERTICAL_RECOVERY_MODE : "off";

  /* STEP 29.5/29.6 (legacy package only): restore world-Y selectively for
   * meshes with objective unit-domain evidence (encoded WEB_height_N or the
   * proven building family); needle guard reverts anomalies. */
  const verticalRecovery = applyOdessaVerticalScaleRecovery(root, recoveryMode);

  /* STEP 29.8 (legacy package only): vertex-level component repair for
   * merged meshes with the "repair-components" verdict. */
  const componentRepair =
    recoveryMode === "off" ? emptySceneComponentRepairResult() : applySceneComponentRepair(root);

  /* STEP 29.4: the source stacks flat OSM decal layers closely along Y,
   * which z-fight at oblique angles. Rank them by authored Y via
   * polygonOffset — depth-only bias, no geometry/color/georeference change.
   * The band/quantum scale with the package (legacy mm vs metric 0.1 m). */
  const decalLayering = applyGroundDecalLayering(root, pkg.decalYScale);

  return {
    root,
    meshCount,
    materialCount: seenMats.size,
    triangleCount: Math.round(triangleCount),
    objectCount,
    visual,
    decalLayering,
    verticalRecovery,
    componentRepair,
  };
}
