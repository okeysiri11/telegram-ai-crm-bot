/**
 * Dispose Three.js object trees safely on tile unload.
 */

import * as THREE from "three";
import { isInternedMaterial } from "./materialIntern";

export function disposeObject3D(root: THREE.Object3D) {
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (mesh.isMesh) {
      mesh.geometry?.dispose();
      const mat = mesh.material;
      const list = Array.isArray(mat) ? mat : mat ? [mat] : [];
      for (const m of list) {
        if (isInternedMaterial(m)) continue;
        m.dispose();
      }
    }
  });
}
