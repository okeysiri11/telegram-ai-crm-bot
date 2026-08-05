/**
 * Intelligence cache + incremental revision — Sprint 29.7.
 */

import type { IntelligenceCycleResult } from "./intelligenceTypes";

let lastCycle: IntelligenceCycleResult | null = null;
let fingerprint = "";
let revision = 0;
let aggregations = new Map<string, number>();

export const intelligenceCache = {
  clear() {
    lastCycle = null;
    fingerprint = "";
    revision = 0;
    aggregations.clear();
  },

  revision() {
    return revision;
  },

  getCycle() {
    return lastCycle;
  },

  putCycle(cycle: IntelligenceCycleResult, fp: string) {
    fingerprint = fp;
    revision = cycle.revision;
    lastCycle = cycle;
    return cycle;
  },

  fingerprintValid(fp: string) {
    return fingerprint === fp && !!lastCycle;
  },

  bumpAggregation(key: string, by = 1) {
    aggregations.set(key, (aggregations.get(key) || 0) + by);
    return aggregations.get(key)!;
  },

  getAggregation(key: string) {
    return aggregations.get(key) || 0;
  },

  stats() {
    return {
      revision,
      hasCycle: !!lastCycle,
      fingerprint,
      aggregationKeys: aggregations.size,
    };
  },
};
