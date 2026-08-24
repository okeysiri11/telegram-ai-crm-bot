/**
 * One-shot scene-graph audit after GLBs attach. Not a per-frame walk.
 */

import * as THREE from "three";
import type { SceneGraphAudit } from "./types";

export function emptySceneGraphAudit(): SceneGraphAudit {
  return {
    object3dCount: 0,
    meshCount: 0,
    namedMeshCount: 0,
    unnamedMeshCount: 0,
    meshesByAsset: {},
    materialsReused: 0,
    uniqueMaterials: 0,
    meshesWithUserData: 0,
    meshesWithAssetId: 0,
  };
}

function materialList(mesh: THREE.Mesh): THREE.Material[] {
  const mat = mesh.material;
  if (!mat) return [];
  return Array.isArray(mat) ? mat : [mat];
}

function hasUserData(obj: THREE.Object3D): boolean {
  const data = obj.userData;
  if (!data) return false;
  return Object.keys(data).length > 0;
}

/**
 * Walk an assembled city root (odessaCityRoot / asset groups).
 * Asset grouping uses mesh.userData.odessaAssetId when present, else nearest named parent.
 */
export function auditSceneGraph(root: THREE.Object3D | null | undefined): SceneGraphAudit {
  const audit = emptySceneGraphAudit();
  if (!root) return audit;

  const materialUse = new Map<string, number>();

  root.traverse((obj) => {
    audit.object3dCount += 1;
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    audit.meshCount += 1;
    if (mesh.name && mesh.name.trim()) audit.namedMeshCount += 1;
    else audit.unnamedMeshCount += 1;
    if (hasUserData(mesh)) audit.meshesWithUserData += 1;

    const assetId =
      typeof mesh.userData?.odessaAssetId === "string"
        ? mesh.userData.odessaAssetId
        : typeof mesh.userData?.assetId === "string"
          ? mesh.userData.assetId
          : "";
    if (assetId) {
      audit.meshesWithAssetId += 1;
      audit.meshesByAsset[assetId] = (audit.meshesByAsset[assetId] ?? 0) + 1;
    } else {
      audit.meshesByAsset["(unattributed)"] = (audit.meshesByAsset["(unattributed)"] ?? 0) + 1;
    }

    for (const mat of materialList(mesh)) {
      const id = mat.uuid;
      materialUse.set(id, (materialUse.get(id) ?? 0) + 1);
    }
  });

  audit.uniqueMaterials = materialUse.size;
  let reused = 0;
  for (const n of materialUse.values()) {
    if (n > 1) reused += 1;
  }
  audit.materialsReused = reused;
  return audit;
}
