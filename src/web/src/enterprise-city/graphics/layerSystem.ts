/**
 * Enterprise City Graphics Engine — Layer System.
 * Sprint CG-2. Separates rendering concerns into independently-enabled layers:
 * Background, Roads, Buildings, Effects, Agents, Selection, UI Overlay, Debug.
 * A layer is a visibility/order record only — it owns no DOM, no store, and no business logic; a
 * consuming screen (e.g. `EnterpriseCityPage.tsx`) decides how each layer's `enabled` flag maps to
 * actual rendered elements. This keeps the layer system reusable by any future City screen without
 * coupling it to one page's markup.
 */

import type { LayerState, RenderLayerId } from "./types";

/** Fixed paint order — lower paints first. Matches the sprint's requested layer list exactly. */
export const DEFAULT_LAYERS: LayerState[] = [
  { id: "background", label: "Background", order: 0, enabled: true },
  { id: "roads", label: "Roads", order: 1, enabled: true },
  { id: "buildings", label: "Buildings", order: 2, enabled: true },
  { id: "effects", label: "Effects", order: 3, enabled: true },
  { id: "agents", label: "Agents", order: 4, enabled: true },
  { id: "selection", label: "Selection", order: 5, enabled: true },
  { id: "ui_overlay", label: "UI Overlay", order: 6, enabled: true },
  { id: "debug", label: "Debug", order: 7, enabled: false },
];

export type LayerRegistry = {
  layers: LayerState[];
  isEnabled: (id: RenderLayerId) => boolean;
  setEnabled: (id: RenderLayerId, enabled: boolean) => LayerRegistry;
  toggle: (id: RenderLayerId) => LayerRegistry;
  ordered: () => LayerState[];
};

function makeRegistry(layers: LayerState[]): LayerRegistry {
  return {
    layers,
    isEnabled(id) {
      return layers.find((l) => l.id === id)?.enabled ?? false;
    },
    setEnabled(id, enabled) {
      return makeRegistry(layers.map((l) => (l.id === id ? { ...l, enabled } : l)));
    },
    toggle(id) {
      return this.setEnabled(id, !this.isEnabled(id));
    },
    ordered() {
      return [...layers].sort((a, b) => a.order - b.order);
    },
  };
}

/** Create a new, independent layer registry — never a shared mutable singleton across screens. */
export function createLayerRegistry(overrides: Partial<Record<RenderLayerId, boolean>> = {}): LayerRegistry {
  const layers = DEFAULT_LAYERS.map((l) => (l.id in overrides ? { ...l, enabled: overrides[l.id]! } : l));
  return makeRegistry(layers);
}

/** Layers a Low-quality graphics setting (`graphicsConfig.ts`) should disable by default. */
export const QUALITY_DISABLED_LAYERS: Record<"low" | "medium", RenderLayerId[]> = {
  low: ["effects", "debug"],
  medium: ["debug"],
};
