/**
 * Stable identity for the loaded Odessa GLB package.
 * Calibration is bound to this fingerprint and must not be reused blindly.
 */

export type ManifestFingerprintInput = {
  cityId?: string;
  version?: string;
  packageId?: string;
  packageFormat?: string;
  tiles?: ReadonlyArray<{ id?: string }>;
  stats?: Record<string, number>;
  cityBounds?: {
    minX: number;
    maxX: number;
    minY?: number;
    maxY?: number;
    minZ: number;
    maxZ: number;
  } | null;
};

function djb2(text: string): string {
  let h = 5381;
  for (let i = 0; i < text.length; i++) {
    h = (h * 33) ^ text.charCodeAt(i);
  }
  return (h >>> 0).toString(16).padStart(8, "0");
}

function stableStats(stats: Record<string, number> | undefined): string {
  if (!stats) return "";
  return Object.keys(stats)
    .sort()
    .map((k) => `${k}:${stats[k]}`)
    .join(",");
}

export function odessaModelFingerprint(manifest: ManifestFingerprintInput | null | undefined): string {
  if (!manifest) return "odessa:unknown";
  const tileIds = (manifest.tiles ?? []).map((t) => t.id ?? "").join("|");
  const b = manifest.cityBounds;
  const bounds = b
    ? `${b.minX},${b.maxX},${b.minY ?? ""},${b.maxY ?? ""},${b.minZ},${b.maxZ}`
    : "";
  const payload = [
    manifest.cityId ?? "",
    manifest.version ?? "",
    manifest.packageId ?? "",
    manifest.packageFormat ?? "",
    String(manifest.tiles?.length ?? 0),
    tileIds,
    stableStats(manifest.stats),
    bounds,
  ].join("\n");
  return `odessa:${djb2(payload)}`;
}
