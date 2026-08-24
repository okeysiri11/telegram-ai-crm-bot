/**
 * Odessa city assembly — global bounds, camera fit, material normalization.
 * All tiles preserve exported transforms; corrections apply only to odessaCityRoot.
 */

import * as THREE from "three";
import type { CityBounds } from "./types";
import { CAMERA_MIN_DISTANCE_M, computeCameraClipRange } from "./cameraNavigation";
import { prepareMeshForPerformance } from "./odessaPerformance";
import { applyMaterialTextureColorSpaces } from "./renderStability";

export type GlobalCityBounds = {
  box: THREE.Box3;
  center: THREE.Vector3;
  size: THREE.Vector3;
  diagonal: number;
};

export function boundsFromCityBounds(b: CityBounds): THREE.Box3 {
  return new THREE.Box3(
    new THREE.Vector3(b.minX, b.minY ?? 0, b.minZ),
    new THREE.Vector3(b.maxX, b.maxY ?? 50, b.maxZ),
  );
}

/** Union manifest extent + actually loaded tile geometry. Does not move tiles. */
export function computeGlobalCityBounds(
  loadedNodes: Iterable<THREE.Object3D>,
  manifestBounds?: CityBounds,
): GlobalCityBounds {
  const box = new THREE.Box3();
  if (manifestBounds) {
    box.union(boundsFromCityBounds(manifestBounds));
  }
  for (const node of loadedNodes) {
    box.expandByObject(node);
  }
  if (box.isEmpty()) {
    box.set(new THREE.Vector3(-500, 0, -500), new THREE.Vector3(500, 50, 500));
  }
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const diagonal = size.length();
  return { box, center, size, diagonal };
}

export type CameraFitResult = {
  position: THREE.Vector3;
  target: THREE.Vector3;
  near: number;
  far: number;
  minDistance: number;
  maxDistance: number;
};

/** Frame the global Odessa bounds — used by fitCameraToOdessa / reset camera. */
export function fitCameraToOdessaBounds(
  bounds: GlobalCityBounds,
  camera: THREE.PerspectiveCamera,
  aspect: number,
  padding = 1.25,
): CameraFitResult {
  const { center, size, diagonal } = bounds;
  const maxDim = Math.max(size.x, size.y, size.z, 1);
  const fov = (camera.fov * Math.PI) / 180;
  const fitHeightDistance = maxDim / (2 * Math.tan(fov / 2));
  const fitWidthDistance = fitHeightDistance / aspect;
  let distance = Math.max(fitHeightDistance, fitWidthDistance) * padding;
  distance = Math.max(distance, diagonal * 0.35);

  const elev = Math.max(size.y * 0.55, maxDim * 0.28);
  const position = new THREE.Vector3(
    center.x + distance * 0.62,
    center.y + elev,
    center.z + distance * 0.62,
  );

  const clip = computeCameraClipRange({ size, diagonal });
  /* Street-level min distance is NOT scaled by city size or clip.near —
   * otherwise the metric (~84 km) package cannot zoom from city → building. */
  const minDistance = CAMERA_MIN_DISTANCE_M;
  const maxDistance = Math.max(diagonal * 2.6, maxDim * 3.2, 2200);

  return {
    position,
    target: center.clone(),
    near: clip.near,
    far: clip.far,
    minDistance,
    maxDistance,
  };
}

export function focusCameraOnPoint(
  point: THREE.Vector3,
  camera: THREE.PerspectiveCamera,
  controlsTarget: THREE.Vector3,
  distanceScale = 0.08,
  boundsDiagonal = 1200,
): { position: THREE.Vector3; target: THREE.Vector3 } {
  const offset = new THREE.Vector3().subVectors(camera.position, controlsTarget);
  let dist = offset.length();
  if (dist < 1) dist = boundsDiagonal * distanceScale;
  else dist = Math.max(dist * 0.55, boundsDiagonal * 0.004);
  offset.normalize().multiplyScalar(dist);
  const target = point.clone();
  const position = target.clone().add(offset);
  position.y = Math.max(position.y, target.y + 2);
  return { position, target };
}

export type MaterialAudit = {
  meshCount: number;
  materialCount: number;
  textureCount: number;
  missingTextureSlots: number;
  vertexColorMeshes: number;
};

export type MaterialNormalizeOptions = {
  enableShadows?: boolean;
  maxAnisotropy?: number;
};

/** Conservative daylight pass — preserve authored materials, fix colorSpace only. */
export function normalizeLoadedMaterials(
  root: THREE.Object3D,
  opts: MaterialNormalizeOptions = {},
): MaterialAudit {
  const enableShadows = opts.enableShadows ?? false;
  const maxAnisotropy = opts.maxAnisotropy ?? 4;
  const audit: MaterialAudit = {
    meshCount: 0,
    materialCount: 0,
    textureCount: 0,
    missingTextureSlots: 0,
    vertexColorMeshes: 0,
  };
  const seenMats = new Set<THREE.Material>();

  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh) return;
    audit.meshCount += 1;
    if (mesh.geometry?.attributes.color) audit.vertexColorMeshes += 1;
    prepareMeshForPerformance(mesh, { enableShadows, maxAnisotropy });

    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const mat of materials) {
      if (!mat || seenMats.has(mat)) continue;
      seenMats.add(mat);
      audit.materialCount += 1;

      const std = mat as THREE.MeshStandardMaterial;
      applyMaterialTextureColorSpaces(mat);
      const texKeys = ["map", "normalMap", "roughnessMap", "metalnessMap", "aoMap", "emissiveMap"] as const;
      for (const key of texKeys) {
        const tex = (mat as THREE.MeshStandardMaterial)[key];
        if (tex) {
          audit.textureCount += 1;
        }
      }
      if (std.isMeshStandardMaterial && !std.map && !std.color) {
        audit.missingTextureSlots += 1;
        std.color = new THREE.Color(0x9aa3ad);
      }
    }
  });

  return audit;
}

export function createTileBoundsHelper(box: THREE.Box3, color = 0x00ff88): THREE.LineSegments {
  const helper = new THREE.Box3Helper(box, new THREE.Color(color));
  helper.name = "tile_bounds_helper";
  return helper;
}

export function tileBoxFromObject(node: THREE.Object3D): THREE.Box3 {
  return new THREE.Box3().setFromObject(node);
}
