/**
 * Runtime health hook — Sprint 27.1 / 28.1.
 * Delegates to Health Service singleton (no per-instance polling).
 */

export type { RuntimeHealthId, RuntimeHealthItem } from "@/enterprise-runtime/types";
export { useRuntimeHealth, toStatusSnapshots } from "@/enterprise-runtime/useRuntimeHealth";
