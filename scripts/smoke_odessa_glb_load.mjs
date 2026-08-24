#!/usr/bin/env node
/**
 * Smoke test: load one Odessa GLB via same fetch+parse path as production.
 * Usage: node scripts/smoke_odessa_glb_load.mjs [port]
 */

import * as THREE from "../src/web/node_modules/three/build/three.module.js";
import { GLTFLoader } from "../src/web/node_modules/three/examples/jsm/loaders/GLTFLoader.js";

const port = process.argv[2] || "5181";
const url = `http://127.0.0.1:${port}/assets/odessa/FINAL_TILE_04_REST/TILE_04_00_REST_BATCH_03.glb`;

const res = await fetch(url);
console.log("HTTP", res.status, res.headers.get("content-type"), res.headers.get("content-length"));
if (!res.ok) process.exit(1);
const ct = res.headers.get("content-type") || "";
if (ct.includes("text/html")) {
  console.error("FAIL: got HTML instead of GLB — check Vite public path");
  process.exit(1);
}
const buf = await res.arrayBuffer();
const magic = new TextDecoder().decode(new Uint8Array(buf, 0, 4));
if (magic !== "glTF") {
  console.error("FAIL: bad magic", magic);
  process.exit(1);
}

await new Promise((resolve, reject) => {
  new GLTFLoader().parse(buf, url, (gltf) => {
    let meshes = 0;
    gltf.scene.traverse((o) => {
      if (o.isMesh) meshes += 1;
    });
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    console.log(
      JSON.stringify(
        {
          assetId: "TILE_04_00_REST_BATCH_03",
          url,
          bytes: buf.byteLength,
          meshCount: meshes,
          bounds: { min: box.min.toArray(), max: box.max.toArray(), center: center.toArray(), size: size.toArray() },
        },
        null,
        2,
      ),
    );
    if (meshes === 0) reject(new Error("no meshes"));
    else resolve(undefined);
  }, reject);
});

console.log("SMOKE PASS");
