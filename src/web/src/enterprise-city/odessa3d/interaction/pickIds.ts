/**
 * Deterministic pick IDs — no Math.random, stable for a runtime session
 * as long as GLB mesh order for an asset does not change.
 */

const UNSAFE = /[^a-zA-Z0-9._-]+/g;

export function sanitizePickToken(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "unnamed";
  const safe = trimmed.replace(UNSAFE, "_").slice(0, 80);
  return safe || "unnamed";
}

export function makePickId(assetId: string, meshIndex: number, meshName?: string): string {
  const asset = sanitizePickToken(assetId || "asset");
  const name = sanitizePickToken(meshName || "unnamed");
  return `pick:${asset}:${meshIndex}:${name}`;
}
