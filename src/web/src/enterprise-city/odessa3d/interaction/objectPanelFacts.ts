/**
 * Safe display facts for the selected-object panel. Missing fields → "Нет данных".
 */

import type { EntityBindingResult, PickableBounds, PickableEntity } from "./types";

export const NO_DATA = "Нет данных";

function fmt(n: number | undefined | null, digits = 2): string {
  if (n == null || !Number.isFinite(n)) return NO_DATA;
  return n.toFixed(digits);
}

function centerFromBounds(bounds?: PickableBounds) {
  if (!bounds) return null;
  return {
    x: (bounds.minX + bounds.maxX) / 2,
    y: (bounds.minY + bounds.maxY) / 2,
    z: (bounds.minZ + bounds.maxZ) / 2,
  };
}

function sizeFromBounds(bounds?: PickableBounds) {
  if (!bounds) return null;
  return {
    x: Math.abs(bounds.maxX - bounds.minX),
    y: Math.abs(bounds.maxY - bounds.minY),
    z: Math.abs(bounds.maxZ - bounds.minZ),
  };
}

export type ObjectPanelFacts = {
  name: string;
  type: string;
  id: string;
  position: { x: string; y: string; z: string };
  size: { x: string; y: string; z: string };
  hasGeometry: boolean;
};

export function objectPanelFacts(
  pickable: PickableEntity | null | undefined,
  binding: EntityBindingResult | null | undefined,
): ObjectPanelFacts {
  const pos = pickable?.position ?? centerFromBounds(pickable?.bounds);
  const size = pickable?.size ?? sizeFromBounds(pickable?.bounds);
  return {
    name: binding?.label || pickable?.displayName || pickable?.meshName || NO_DATA,
    type: binding?.kind || pickable?.classification || NO_DATA,
    id: binding?.enterpriseEntityId || pickable?.pickId || NO_DATA,
    position: {
      x: fmt(pos?.x),
      y: fmt(pos?.y),
      z: fmt(pos?.z),
    },
    size: {
      x: fmt(size?.x),
      y: fmt(size?.y),
      z: fmt(size?.z),
    },
    hasGeometry: !!pos && !!size,
  };
}
