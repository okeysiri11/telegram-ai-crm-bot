/**
 * Active pickable mesh registry. Cached on activate; cleared on unload/dispose.
 * Does not retain disposed GLB object graphs.
 */

import * as THREE from "three";
import { bindPickableFromLookup } from "./entityBinding";
import { classificationOfMesh, isInteractivePickMesh } from "./pickFilter";
import { makePickId } from "./pickIds";
import { BROADPHASE_MESH_THRESHOLD, rayIntersectsBox } from "./pickRaycast";
import type { PickableBounds, PickableEntity } from "./types";

export type RegisterAssetInput = {
  assetId: string;
  root: THREE.Object3D;
  layerId?: string;
  entityRefs?: string[];
  manifestEntityRef?: string;
};

type Entry = {
  entity: PickableEntity;
  object: THREE.Object3D;
};

function meshMaterialName(mesh: THREE.Mesh): string | undefined {
  const mat = mesh.material;
  if (!mat) return undefined;
  if (Array.isArray(mat)) return mat[0]?.name || undefined;
  return mat.name || undefined;
}

function classificationOf(mesh: THREE.Mesh): string | undefined {
  return classificationOfMesh(mesh);
}

function boundsFromObject(obj: THREE.Object3D): PickableBounds | undefined {
  const box = new THREE.Box3().setFromObject(obj);
  if (box.isEmpty()) return undefined;
  return {
    minX: box.min.x,
    maxX: box.max.x,
    minY: box.min.y,
    maxY: box.max.y,
    minZ: box.min.z,
    maxZ: box.max.z,
  };
}

function meshDisplayName(mesh: THREE.Mesh): string | undefined {
  const md = mesh.userData?.metadata;
  if (md && typeof md === "object" && typeof (md as { name?: unknown }).name === "string") {
    const n = (md as { name: string }).name.trim();
    if (n) return n;
  }
  if (typeof mesh.userData?.name === "string" && mesh.userData.name.trim()) {
    return mesh.userData.name.trim();
  }
  return mesh.name?.trim() || undefined;
}

function centerAndSize(bounds?: PickableBounds): {
  position?: { x: number; y: number; z: number };
  size?: { x: number; y: number; z: number };
} {
  if (!bounds) return {};
  return {
    position: {
      x: (bounds.minX + bounds.maxX) / 2,
      y: (bounds.minY + bounds.maxY) / 2,
      z: (bounds.minZ + bounds.maxZ) / 2,
    },
    size: {
      x: Math.abs(bounds.maxX - bounds.minX),
      y: Math.abs(bounds.maxY - bounds.minY),
      z: Math.abs(bounds.maxZ - bounds.minZ),
    },
  };
}

export class PickRegistry {
  private byPickId = new Map<string, Entry>();
  private byUuid = new Map<string, string>();
  private byAsset = new Map<string, string[]>();
  private assetBoxes = new Map<string, THREE.Box3>();
  private candidateCache: THREE.Object3D[] = [];
  private candidatesDirty = true;

  size(): number {
    return this.byPickId.size;
  }

  has(pickId: string): boolean {
    return this.byPickId.has(pickId);
  }

  get(pickId: string): PickableEntity | undefined {
    return this.byPickId.get(pickId)?.entity;
  }

  getObject(pickId: string): THREE.Object3D | undefined {
    const entry = this.byPickId.get(pickId);
    if (!entry) return undefined;
    const obj = entry.object;
    if (!obj.parent && obj.type !== "Scene") {
      /* detached after unload — treat as missing */
      return undefined;
    }
    return obj;
  }

  list(): PickableEntity[] {
    return [...this.byPickId.values()].map((e) => e.entity);
  }

  resolveFromObject(hit: THREE.Object3D | null | undefined): PickableEntity | undefined {
    let node: THREE.Object3D | null = hit ?? null;
    while (node) {
      const pickId = this.byUuid.get(node.uuid);
      if (pickId) return this.byPickId.get(pickId)?.entity;
      node = node.parent;
    }
    return undefined;
  }

  registerAsset(input: RegisterAssetInput): number {
    this.unregisterAsset(input.assetId);
    const pickIds: string[] = [];
    let meshIndex = 0;
    const box = new THREE.Box3();

    input.root.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh || !mesh.geometry) return;
      if (!isInteractivePickMesh(mesh).ok) return;

      mesh.userData.odessaAssetId = input.assetId;
      const pickId = makePickId(input.assetId, meshIndex, mesh.name);
      meshIndex += 1;
      if (this.byPickId.has(pickId)) return;

      const binding = bindPickableFromLookup({
        pickId,
        assetId: input.assetId,
        meshName: mesh.name || undefined,
        entityRefs: input.entityRefs,
        manifestEntityRef: input.manifestEntityRef,
      });

      const bounds = boundsFromObject(mesh);
      const xyz = centerAndSize(bounds);
      const entity: PickableEntity = {
        pickId,
        assetId: input.assetId,
        objectUuid: mesh.uuid,
        meshName: mesh.name || undefined,
        displayName: meshDisplayName(mesh),
        materialName: meshMaterialName(mesh),
        layerId: input.layerId,
        classification: classificationOf(mesh),
        enterpriseEntityId: binding.enterpriseEntityId,
        bindingStatus: binding.status,
        bounds,
        position: xyz.position,
        size: xyz.size,
      };

      this.byPickId.set(pickId, { entity, object: mesh });
      this.byUuid.set(mesh.uuid, pickId);
      pickIds.push(pickId);
    });

    if (pickIds.length === 0) {
      /* still track empty asset so unregister is a no-op */
      this.byAsset.set(input.assetId, []);
    } else {
      this.byAsset.set(input.assetId, pickIds);
    }
    box.setFromObject(input.root);
    if (!box.isEmpty()) this.assetBoxes.set(input.assetId, box);
    this.candidatesDirty = true;
    return pickIds.length;
  }

  unregisterAsset(assetId: string): void {
    const ids = this.byAsset.get(assetId);
    if (ids) {
      for (const pickId of ids) {
        const entry = this.byPickId.get(pickId);
        if (entry) {
          this.byUuid.delete(entry.object.uuid);
          this.byPickId.delete(pickId);
        }
      }
    }
    this.byAsset.delete(assetId);
    this.assetBoxes.delete(assetId);
    this.candidatesDirty = true;
  }

  clear(): void {
    this.byPickId.clear();
    this.byUuid.clear();
    this.byAsset.clear();
    this.assetBoxes.clear();
    this.candidateCache = [];
    this.candidatesDirty = true;
  }

  candidates(): THREE.Object3D[] {
    if (!this.candidatesDirty) return this.candidateCache;
    const list: THREE.Object3D[] = [];
    for (const entry of this.byPickId.values()) {
      const obj = entry.object;
      if (!obj.visible) continue;
      if (!obj.parent) continue;
      list.push(obj);
    }
    this.candidateCache = list;
    this.candidatesDirty = false;
    return list;
  }

  markDirty(): void {
    this.candidatesDirty = true;
  }

  /**
   * If the pickable count is high, first reject assets whose AABB misses the ray.
   */
  candidatesForRay(ray: THREE.Ray): THREE.Object3D[] {
    const all = this.candidates();
    if (all.length <= BROADPHASE_MESH_THRESHOLD) return all;
    const allowed = new Set<string>();
    for (const [assetId, box] of this.assetBoxes) {
      if (rayIntersectsBox(ray, box)) allowed.add(assetId);
    }
    if (allowed.size === 0) return all;
    return all.filter((obj) => {
      const assetId = obj.userData?.odessaAssetId;
      return typeof assetId === "string" && allowed.has(assetId);
    });
  }

  isObjectLive(obj: THREE.Object3D | undefined): boolean {
    if (!obj) return false;
    if (obj.parent) return true;
    return this.byUuid.has(obj.uuid);
  }
}
