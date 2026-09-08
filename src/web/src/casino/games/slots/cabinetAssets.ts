// Odessa Prime Slots — image-first cabinet assets (Phase 4.3 architecture,
// Phase 4.4A photoreal cutouts at the same public paths).
import {
  CABINET_ASPECT,
  CABINET_ASPECT_BY_ID,
  CABINET_SCREEN_RECT,
  CABINET_SCREEN_RECT_BY_ID,
} from "./cabinetGeometry.generated";
import type { SlotGameDefinition } from "./slotTypes";

export const HALL_BACKGROUND_URL = "/assets/casino/slots/hall-bg.jpg";
export const CHAIR_URL = "/assets/casino/slots/chair.png";

export function cabinetImageUrl(def: Pick<SlotGameDefinition, "id">): string {
  return `/assets/casino/slots/cabinets/${def.id}.png`;
}

export function cabinetScreenRect(def: Pick<SlotGameDefinition, "id" | "cabinetVariant">) {
  return CABINET_SCREEN_RECT_BY_ID[def.id] ?? CABINET_SCREEN_RECT[def.cabinetVariant];
}

export function cabinetAspectRatio(def: Pick<SlotGameDefinition, "id" | "cabinetVariant">): string {
  const sized = CABINET_ASPECT_BY_ID[def.id] ?? CABINET_ASPECT[def.cabinetVariant];
  return `${sized.w} / ${sized.h}`;
}
