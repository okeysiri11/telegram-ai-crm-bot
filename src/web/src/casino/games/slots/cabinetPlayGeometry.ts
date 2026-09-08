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
  history: OverlayRect;
};

export type SeatedCrop = {
  heightPct: number;
  bottomPct: number;
};

const RADIUS: Record<SlotGameDefinition["cabinetVariant"], number> = {
  curved: 16,
  square: 8,
  slim: 12,
};

/** Extra inset so live reels stay inside the monitor glass, not on the bezel. */
const SEATED_GLASS_INSET: Record<string, { left: number; top: number; right: number; bottom: number }> = {
  "olympus-crown": { left: 2.35, top: 5.85, right: 2.35, bottom: 2.15 },
  "lady-emerald": { left: 1.95, top: 2.1, right: 1.95, bottom: 1.85 },
  "pharaohs-book": { left: 2.0, top: 2.15, right: 2.0, bottom: 1.9 },
  "buffalo-fortune": { left: 2.0, top: 2.35, right: 2.0, bottom: 1.9 },
  "candy-fortune": { left: 2.05, top: 2.2, right: 2.05, bottom: 1.95 },
  "big-catch": { left: 2.05, top: 3.35, right: 2.05, bottom: 1.9 },
};

const SEATED_DECK_NUDGE: Record<string, { touchGap: number; deckGap: number; spinLeftFactor: number }> = {
  "olympus-crown": { touchGap: 2.35, deckGap: 11.2, spinLeftFactor: 0.735 },
  "lady-emerald": { touchGap: 2.1, deckGap: 10.4, spinLeftFactor: 0.73 },
  "pharaohs-book": { touchGap: 2.2, deckGap: 10.6, spinLeftFactor: 0.73 },
  "buffalo-fortune": { touchGap: 2.2, deckGap: 10.5, spinLeftFactor: 0.73 },
  "candy-fortune": { touchGap: 2.15, deckGap: 10.2, spinLeftFactor: 0.72 },
  "big-catch": { touchGap: 2.1, deckGap: 10.3, spinLeftFactor: 0.72 },
};

const SEATED_CROP: Record<string, SeatedCrop> = {
  "olympus-crown": { heightPct: 150, bottomPct: -20 },
  "lady-emerald": { heightPct: 168, bottomPct: -14 },
  "pharaohs-book": { heightPct: 168, bottomPct: -12 },
  "buffalo-fortune": { heightPct: 166, bottomPct: -14 },
  "candy-fortune": { heightPct: 162, bottomPct: -20 },
  "big-catch": { heightPct: 160, bottomPct: -22 },
};

export function insetOverlay(
  rect: OverlayRect,
  pad: { left: number; top: number; right: number; bottom: number } | number,
  yPct?: number,
): OverlayRect {
  const inset =
    typeof pad === "number"
      ? { left: pad, top: yPct ?? pad, right: pad, bottom: yPct ?? pad }
      : pad;
  return {
    ...rect,
    leftPct: rect.leftPct + inset.left,
    topPct: rect.topPct + inset.top,
    widthPct: rect.widthPct - inset.left - inset.right,
    heightPct: rect.heightPct - inset.top - inset.bottom,
  };
}

export function overlayWithinUnitSquare(rect: OverlayRect): boolean {
  return (
    rect.leftPct >= 0 &&
    rect.topPct >= 0 &&
    rect.widthPct > 0 &&
    rect.heightPct > 0 &&
    rect.leftPct + rect.widthPct <= 100 &&
    rect.topPct + rect.heightPct <= 100
  );
}

export function overlayContainedIn(outer: OverlayRect, inner: OverlayRect): boolean {
  return (
    inner.leftPct >= outer.leftPct &&
    inner.topPct >= outer.topPct &&
    inner.leftPct + inner.widthPct <= outer.leftPct + outer.widthPct &&
    inner.topPct + inner.heightPct <= outer.topPct + outer.heightPct
  );
}

export function seatedCrop(def: Pick<SlotGameDefinition, "id">): SeatedCrop {
  return SEATED_CROP[def.id] ?? { heightPct: 164, bottomPct: -22 };
}

export function cabinetPlayLayout(def: SlotGameDefinition): CabinetPlayLayout {
  const glass = cabinetScreenRect(def);
  const radius = RADIUS[def.cabinetVariant];
  const inset = SEATED_GLASS_INSET[def.id] ?? { left: 2, top: 2.1, right: 2, bottom: 1.9 };
  const nudge = SEATED_DECK_NUDGE[def.id] ?? { touchGap: 2.2, deckGap: 10.5, spinLeftFactor: 0.73 };
  const screen = { ...insetOverlay(glass, inset), borderRadius: radius };
  const touchTop = glass.topPct + glass.heightPct + nudge.touchGap;
  const touch: OverlayRect = {
    leftPct: glass.leftPct + 6.5,
    topPct: touchTop,
    widthPct: Math.max(30, glass.widthPct - 13),
    heightPct: 5.4,
    borderRadius: 6,
  };
  const deck: OverlayRect = {
    leftPct: glass.leftPct + 0.4,
    topPct: touchTop + nudge.deckGap,
    widthPct: glass.widthPct * 0.7,
    heightPct: 10.8,
    borderRadius: 8,
  };
  const spin: OverlayRect = {
    leftPct: glass.leftPct + glass.widthPct * nudge.spinLeftFactor,
    topPct: deck.topPct - 0.35,
    widthPct: Math.min(15.5, glass.widthPct * 0.24),
    heightPct: deck.heightPct * 1.08,
    borderRadius: 999,
  };
  const history: OverlayRect = {
    leftPct: touch.leftPct,
    topPct: glass.topPct + glass.heightPct + 0.35,
    widthPct: touch.widthPct,
    heightPct: Math.min(14, deck.topPct - (glass.topPct + glass.heightPct) - 0.4),
    borderRadius: 8,
  };
  return { screen, touch, deck, spin, history };
}
