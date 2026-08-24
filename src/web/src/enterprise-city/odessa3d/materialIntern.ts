/**
 * Safe runtime GPU resource intern — identical untextured materials only.
 * Does not merge meshes or rewrite GLB geometry.
 */

import * as THREE from "three";

const WATER_NAME = /water|sea|ocean|bay|river|lake|canal/i;

export function materialInternKey(mat: THREE.Material): string | null {
  const std = mat as THREE.MeshStandardMaterial;
  if (!std.isMeshStandardMaterial) return null;
  if (WATER_NAME.test(std.name || "")) return null;
  if (std.map || std.normalMap || std.roughnessMap || std.metalnessMap || std.aoMap || std.emissiveMap) {
    return null;
  }
  const emissiveHex = std.emissive ? std.emissive.getHex() : 0;
  const emissiveIntensity = std.emissiveIntensity ?? 1;
  if (emissiveHex !== 0 && emissiveIntensity > 0.01) return null;
  if (std.transparent && (std.opacity ?? 1) < 0.999) {
    /* transparent materials may share only when opacity+blending match — encoded in key below */
  }
  const color = std.color ? std.color.getHex() : 0;
  const metal = +(std.metalness ?? 0).toFixed(3);
  const rough = +(std.roughness ?? 1).toFixed(3);
  const opacity = +(std.opacity ?? 1).toFixed(3);
  const blending = std.blending ?? THREE.NormalBlending;
  const depthWrite = std.depthWrite === false ? 0 : 1;
  const depthTest = std.depthTest === false ? 0 : 1;
  const side = std.side ?? THREE.FrontSide;
  /* STEP 29.4: decal ranks live in polygonOffset — never merge across ranks. */
  const po = std.polygonOffset ? `${std.polygonOffsetFactor ?? 0},${std.polygonOffsetUnits ?? 0}` : "0";
  return `${std.name}|${color}|${metal}|${rough}|${side}|${std.transparent ? 1 : 0}|${opacity}|${blending}|${depthWrite}|${depthTest}|${po}`;
}

export class MaterialInternCache {
  private cache = new Map<string, THREE.Material>();
  private refs = new Map<THREE.Material, number>();
  interned = 0;

  intern(mat: THREE.Material): THREE.Material {
    const key = materialInternKey(mat);
    if (!key) return mat;
    const existing = this.cache.get(key);
    if (existing && existing !== mat) {
      this.retain(existing);
      this.interned += 1;
      return existing;
    }
    mat.userData.odessaInterned = true;
    this.cache.set(key, mat);
    this.refs.set(mat, (this.refs.get(mat) ?? 0) + 1);
    return mat;
  }

  retain(mat: THREE.Material) {
    this.refs.set(mat, (this.refs.get(mat) ?? 0) + 1);
  }

  release(mat: THREE.Material) {
    const n = (this.refs.get(mat) ?? 1) - 1;
    if (n <= 0) {
      this.refs.delete(mat);
      for (const [k, v] of this.cache) {
        if (v === mat) this.cache.delete(k);
      }
      if (mat.userData.odessaInterned) mat.dispose();
    } else {
      this.refs.set(mat, n);
    }
  }

  applyToRoot(root: THREE.Object3D): number {
    let replaced = 0;
    root.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh) return;
      if (Array.isArray(mesh.material)) {
        mesh.material = mesh.material.map((m) => {
          const next = this.intern(m);
          if (next !== m) replaced += 1;
          return next;
        });
      } else if (mesh.material) {
        const next = this.intern(mesh.material);
        if (next !== mesh.material) {
          mesh.material = next;
          replaced += 1;
        }
      }
    });
    return replaced;
  }

  dispose() {
    for (const mat of this.cache.values()) mat.dispose();
    this.cache.clear();
    this.refs.clear();
    this.interned = 0;
  }
}

export function isInternedMaterial(mat: THREE.Material): boolean {
  return !!mat.userData?.odessaInterned;
}
