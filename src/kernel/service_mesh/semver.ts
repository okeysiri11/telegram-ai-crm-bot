/**
 * SemVer helpers for mesh version compatibility.
 */
export function parseSemVer(
  version: string,
): { major: number; minor: number; patch: number } {
  const cleaned = version.trim().replace(/^v/i, "");
  const parts = cleaned.split(".");
  const major = Number(parts[0] ?? 0);
  const minor = Number(parts[1] ?? 0);
  const patch = Number((parts[2] ?? "0").split("-")[0] ?? 0);
  if ([major, minor, patch].some((n) => Number.isNaN(n))) {
    throw new Error(`Invalid semver: ${version}`);
  }
  return { major, minor, patch };
}

export function compareSemVer(a: string, b: string): number {
  const pa = parseSemVer(a);
  const pb = parseSemVer(b);
  if (pa.major !== pb.major) return pa.major - pb.major;
  if (pa.minor !== pb.minor) return pa.minor - pb.minor;
  return pa.patch - pb.patch;
}

export function isVersionCompatible(
  version: string,
  range?: {
    readonly min?: string;
    readonly maxExclusive?: string;
    readonly exact?: string;
  },
): boolean {
  if (!range) return true;
  if (range.exact !== undefined) {
    return compareSemVer(version, range.exact) === 0;
  }
  if (range.min !== undefined && compareSemVer(version, range.min) < 0) {
    return false;
  }
  if (
    range.maxExclusive !== undefined &&
    compareSemVer(version, range.maxExclusive) >= 0
  ) {
    return false;
  }
  return true;
}
