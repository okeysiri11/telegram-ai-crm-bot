/**
 * Cheap GLB container inspection. Worker-safe as a pure ArrayBuffer read,
 * but executed on the main thread because transferring a 20–25 MB buffer
 * would detach it before GLTFLoader.parse (or force a full copy).
 */

export const GLB_MAGIC = "glTF";
const JSON_CHUNK = 0x4e4f534a;
const BIN_CHUNK = 0x004e4942;

export type GlbHeaderInfo = {
  magic: string;
  version: number;
  length: number;
  jsonChunkBytes: number;
  binChunkBytes: number;
};

export function inspectGlbHeader(buffer: ArrayBuffer): GlbHeaderInfo {
  if (buffer.byteLength < 12) {
    throw new Error(`INVALID_GLB_MAGIC:short ${buffer.byteLength}`);
  }
  const magic = new TextDecoder().decode(new Uint8Array(buffer, 0, 4));
  if (magic !== GLB_MAGIC) {
    throw new Error(`INVALID_GLB_MAGIC:${magic}`);
  }
  const view = new DataView(buffer);
  const version = view.getUint32(4, true);
  const length = view.getUint32(8, true);
  let jsonChunkBytes = 0;
  let binChunkBytes = 0;
  if (buffer.byteLength >= 20) {
    jsonChunkBytes = view.getUint32(12, true);
    const jsonType = view.getUint32(16, true);
    if (jsonType !== JSON_CHUNK && jsonType !== 0) {
      /* still a GLB; chunk type mismatch is informational */
    }
    const binHeader = 20 + jsonChunkBytes;
    if (buffer.byteLength >= binHeader + 8) {
      binChunkBytes = new DataView(buffer, binHeader).getUint32(0, true);
      const binType = new DataView(buffer, binHeader).getUint32(4, true);
      if (binType !== BIN_CHUNK && binType !== 0) {
        /* informational */
      }
    }
  }
  return { magic, version, length, jsonChunkBytes, binChunkBytes };
}

/**
 * Honest worker feasibility. Full GLTFLoader.parse is NOT implemented in a worker:
 * it constructs live Three.js Object3D / BufferGeometry / Material / Texture graphs
 * that are not structured-cloneable as GPU objects. Transferring the source
 * ArrayBuffer detaches it for the subsequent main-thread parse.
 */
export const GLTF_WORKER_FEASIBILITY = {
  fullGltfParseInWorker: false,
  reason:
    "GLTFLoader.parse creates Three.js scene graphs that cannot round-trip through postMessage; transferring the GLB ArrayBuffer detaches it for the required main-thread parse.",
  safeOnWorker: ["glb header inspect", "chunk length extraction", "manifest enrichment"] as const,
  requiresSharedArrayBuffer: false,
  requiresCrossOriginIsolation: false,
  requiresWebGPU: false,
} as const;
