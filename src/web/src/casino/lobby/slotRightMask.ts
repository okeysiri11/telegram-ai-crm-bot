import { HALL_ART } from "./hallZones";

/**
 * TEMPORARY development-only flag. Must stay false in production.
 * When true (and import.meta.env.DEV), the slots PNG mask is tinted magenta.
 */
export const DEBUG_SLOT_MASK = false;

/** Photographic cut-out used only for DEV mask inspection. Not the hover paint. */
export const SLOTS_MASK = {
  src: "/assets/casino/lobby/hall-slots-foreground.png",
  width: HALL_ART.width,
  height: HALL_ART.height,
} as const;

/** Build-time gold contour. Hover paints this PNG only — no interior wash. */
export const SLOTS_GOLD_EDGE = {
  src: "/assets/casino/lobby/hall-slots-gold-edge.png",
  width: HALL_ART.width,
  height: HALL_ART.height,
} as const;

export function slotsMaskReady(): boolean {
  return SLOTS_MASK.width === HALL_ART.width && SLOTS_MASK.height === HALL_ART.height;
}
