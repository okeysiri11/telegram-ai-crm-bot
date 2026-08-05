/**
 * Visualization layer registry — Sprint 29.5.
 */

import type { VisualizationLayer, VisualizationLayerId, LodTier } from "./cityVisualizationTypes";

const DEFAULT_LAYERS: VisualizationLayer[] = [
  { id: "districts", label: "Districts", enabled: true, order: 10, lodMin: "far" },
  { id: "buildings", label: "Buildings", enabled: true, order: 20, lodMin: "far" },
  { id: "companies", label: "Companies", enabled: true, order: 30, lodMin: "medium" },
  { id: "assets", label: "Assets", enabled: true, order: 40, lodMin: "medium" },
  { id: "citizens", label: "Citizens", enabled: true, order: 50, lodMin: "near" },
  { id: "activities", label: "Activities", enabled: true, order: 60, lodMin: "near" },
  { id: "traffic", label: "Traffic", enabled: false, order: 70, lodMin: "near" },
  { id: "overlays", label: "Overlays", enabled: true, order: 80, lodMin: "detail" },
];

const LOD_RANK: Record<LodTier, number> = {
  far: 0,
  medium: 1,
  near: 2,
  detail: 3,
};

let layers = new Map<VisualizationLayerId, VisualizationLayer>();

function seed() {
  layers = new Map(DEFAULT_LAYERS.map((l) => [l.id, { ...l }]));
}

seed();

export const visualizationRegistry = {
  reset() {
    seed();
  },

  list() {
    return [...layers.values()].sort((a, b) => a.order - b.order);
  },

  get(id: VisualizationLayerId) {
    return layers.get(id);
  },

  setEnabled(id: VisualizationLayerId, enabled: boolean) {
    const cur = layers.get(id);
    if (!cur) return undefined;
    const next = { ...cur, enabled };
    layers.set(id, next);
    return next;
  },

  enabledForLod(lod: LodTier) {
    const rank = LOD_RANK[lod];
    return this.list().filter((l) => l.enabled && LOD_RANK[l.lodMin] <= rank);
  },

  lodRank(tier: LodTier) {
    return LOD_RANK[tier];
  },
};
