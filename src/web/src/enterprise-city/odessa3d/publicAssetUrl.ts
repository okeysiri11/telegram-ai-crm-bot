/**
 * Canonical public asset URLs — always rooted at Vite public dir, never relative to React route.
 */

const ODESSA_ROOT = "/assets/odessa";

export function resolvePublicAssetUrl(pathOrUrl: string): string {
  const raw = pathOrUrl.trim().replace(/\\/g, "/");
  if (raw.startsWith("file://") || raw.includes("/Users/") || raw.includes("~/")) {
    throw new Error(`invalid_local_path:${raw}`);
  }

  const base = import.meta.env.BASE_URL || "/";
  const baseNorm = base.endsWith("/") ? base.slice(0, -1) : base;

  if (raw.startsWith("http://") || raw.startsWith("https://")) return raw;

  if (raw.startsWith(`${ODESSA_ROOT}/`) || raw === ODESSA_ROOT) {
    return baseNorm && baseNorm !== "/" ? `${baseNorm}${raw}` : raw;
  }

  if (raw.startsWith("/")) {
    return baseNorm && baseNorm !== "/" ? `${baseNorm}${raw}` : raw;
  }

  const rel = raw.replace(/^\/+/, "");
  const path = `${ODESSA_ROOT}/${rel}`;
  return baseNorm && baseNorm !== "/" ? `${baseNorm}${path}` : path;
}

export const ODESSA_MANIFEST_URL = resolvePublicAssetUrl("odessa_manifest.json");
