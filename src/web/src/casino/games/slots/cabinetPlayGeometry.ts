import { cabinetScreenRect } from "./cabinetAssets";
import type { SlotGameDefinition } from "./slotTypes";

export type OverlayRect = {
  leftPct: number;
  topPct: number;
  widthPct: number;
  heightPct: number;
  borderRadius?: number;
};

export type CabinetPlayLayout = {
  screen: OverlayRect;
  touch: OverlayRect;
  deck: OverlayRect;
  spin: OverlayRect;
};

const RADIUS: Record<SlotGameDefinition["cabinetVariant"], number> = {
  curved: 16,
  square: 8,
  slim: 12,
};

export function cabinetPlayLayout(def: SlotGameDefinition): CabinetPlayLayout {
  const screen = cabinetScreenRect(def);
  const radius = RADIUS[def.cabinetVariant];
  const touchTop = screen.topPct + screen.heightPct + 2.1;
  const touch: OverlayRect = {
    leftPct: screen.leftPct + 7,
    topPct: touchTop,
    widthPct: Math.max(32, screen.widthPct - 14),
    heightPct: 6.2,
    borderRadius: 6,
  };
  const deck: OverlayRect = {
    leftPct: screen.leftPct - 0.6,
    topPct: touchTop + 6.8,
    widthPct: screen.widthPct + 1.2,
    heightPct: 11.2,
    borderRadius: 8,
  };
  const spin: OverlayRect = {
    leftPct: deck.leftPct + deck.widthPct * 0.72,
    topPct: deck.topPct + 0.4,
    widthPct: Math.min(16, deck.widthPct * 0.26),
    heightPct: deck.heightPct * 0.9,
    borderRadius: 999,
  };
  return {
    screen: { ...screen, borderRadius: radius },
    touch,
    deck,
    spin,
  };
}
