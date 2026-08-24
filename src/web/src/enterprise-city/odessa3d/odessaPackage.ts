/**
 * STEP 29.9 — Odessa asset package registry and A/B selector.
 *
 * Two packages exist side by side:
 *
 *  - REBUILT_METRIC (default, production): the 45 GLBs rebuilt by
 *    scripts/step29_9_build_metric_package.mjs. 1 world unit = 1 meter.
 *    The vendor FBX authored meters but declared centimeters, so the
 *    Blender export carried a wrong uniform 0.01 node scale; the rebuild
 *    removes it (translation ×100, scale → 1, geometry buffers untouched).
 *    This package needs NO runtime geometry recovery of any kind.
 *
 *  - CURRENT_BROKEN (rollback only): the original Blender export with the
 *    1/100 unit defect plus the STEP 29.5–29.8 runtime recovery chain.
 *
 * Selection is a DEV concern: localStorage override for instant A/B
 * comparison, defaulting to REBUILT_METRIC.
 */

export type OdessaPackageId = "REBUILT_METRIC" | "CURRENT_BROKEN";

export type OdessaPackageProfile = {
  id: OdessaPackageId;
  label: string;
  manifestUrl: string;
  /** World units per meter (1 = metric package, 0.01 = legacy 1/100 city). */
  worldUnitsPerMeter: number;
  /**
   * Authored-Y scale of the ground-decal stack relative to the STEP 29.4
   * reference (legacy package). The metric package multiplies every authored
   * offset by 100, so the decal band/thickness/rank quantum scale with it.
   */
  decalYScale: number;
  /** STEP 29.5–29.8 vertical recovery + component repair (legacy only). */
  runtimeGeometryRecovery: boolean;
};

export const ODESSA_PACKAGES: Record<OdessaPackageId, OdessaPackageProfile> = {
  REBUILT_METRIC: {
    id: "REBUILT_METRIC",
    label: "Rebuilt metric (1 unit = 1 m)",
    manifestUrl: "/assets/odessa_metric/odessa_manifest.json",
    worldUnitsPerMeter: 1,
    decalYScale: 100,
    runtimeGeometryRecovery: false,
  },
  CURRENT_BROKEN: {
    id: "CURRENT_BROKEN",
    label: "Legacy 1/100 export (rollback)",
    manifestUrl: "/assets/odessa/odessa_manifest.json",
    worldUnitsPerMeter: 0.01,
    decalYScale: 1,
    runtimeGeometryRecovery: true,
  },
};

export const ODESSA_DEFAULT_PACKAGE: OdessaPackageId = "REBUILT_METRIC";

const STORAGE_KEY = "odessa3d.package";

/** In-memory selection — works in node/tests; mirrored to localStorage when available. */
let memoryPackageId: OdessaPackageId | null = null;

export function readStoredPackageId(): OdessaPackageId | null {
  if (memoryPackageId) return memoryPackageId;
  try {
    const raw = globalThis.localStorage?.getItem(STORAGE_KEY);
    return raw && raw in ODESSA_PACKAGES ? (raw as OdessaPackageId) : null;
  } catch {
    return null;
  }
}

export function storePackageId(id: OdessaPackageId | null): void {
  memoryPackageId = id;
  try {
    if (id === null) globalThis.localStorage?.removeItem(STORAGE_KEY);
    else globalThis.localStorage?.setItem(STORAGE_KEY, id);
  } catch {
    /* storage unavailable (SSR/private mode) — in-memory selection applies */
  }
}

export function activeOdessaPackage(): OdessaPackageProfile {
  return ODESSA_PACKAGES[readStoredPackageId() ?? ODESSA_DEFAULT_PACKAGE];
}
