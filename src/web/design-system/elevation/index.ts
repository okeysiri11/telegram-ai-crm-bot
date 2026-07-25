import { shadows, zIndex } from "../tokens";

export const elevationSystem = {
  levels: {
    flat: { shadow: shadows.none, z: zIndex.base },
    raised: { shadow: shadows.sm, z: zIndex.base },
    overlay: { shadow: shadows.md, z: zIndex.dropdown },
    modal: { shadow: shadows.lg, z: zIndex.modal },
    focus: { shadow: shadows.focus, z: zIndex.base },
  },
  zIndex,
} as const;
