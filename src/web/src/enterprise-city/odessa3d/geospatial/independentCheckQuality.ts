/**
 * STEP 30.5 independent-check quality. Control fit is diagnostic only.
 */

export type IndependentCheckQuality = "EXCELLENT" | "GOOD" | "ACCEPTABLE" | "FAILED" | "BLOCKED";

export function qualityFromIndependentCheck(rmsM: number | null, p95M: number | null): IndependentCheckQuality {
  if (rmsM == null || p95M == null || !Number.isFinite(rmsM) || !Number.isFinite(p95M)) return "BLOCKED";
  if (rmsM <= 5 && p95M <= 10) return "EXCELLENT";
  if (rmsM <= 10 && p95M <= 20) return "GOOD";
  if (rmsM <= 20 && p95M <= 35) return "ACCEPTABLE";
  return "FAILED";
}

export function canPersistIndependent(quality: IndependentCheckQuality): boolean {
  return quality === "EXCELLENT" || quality === "GOOD" || quality === "ACCEPTABLE";
}

export function percentileSorted(sorted: readonly number[], p: number): number | null {
  if (!sorted.length) return null;
  const idx = (sorted.length - 1) * p;
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo];
  return sorted[lo] * (hi - idx) + sorted[hi] * (idx - lo);
}

export function rms(values: readonly number[]): number | null {
  if (!values.length) return null;
  return Math.sqrt(values.reduce((s, n) => s + n * n, 0) / values.length);
}
