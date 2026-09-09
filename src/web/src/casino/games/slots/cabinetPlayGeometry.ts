import { cabinetScreenRect } from "./cabinetAssets";
import { boundsOf, cabinetControls, screenMetersRect } from "./cabinetControls";
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
  const screen = { ...insetOverlay(glass, inset), borderRadius: radius };
  const controls = cabinetControls(def);
  const spinControl = controls.find((item) => item.action === "spin");
  const paintedBets = controls.filter((item) => item.action === "bet" && item.painted);
  const deck = boundsOf(paintedBets.length ? paintedBets : controls);
  const touch = screenMetersRect(def, screen);
  const spin: OverlayRect = spinControl
    ? {
        leftPct: spinControl.leftPct,
        topPct: spinControl.topPct,
        widthPct: spinControl.widthPct,
        heightPct: spinControl.heightPct,
        borderRadius: spinControl.borderRadius,
      }
    : deck;
  const history: OverlayRect = {
    leftPct: screen.leftPct + 8,
    topPct: screen.topPct + 4,
    widthPct: Math.max(28, screen.widthPct - 16),
    heightPct: 16,
    borderRadius: 8,
  };
  return { screen, touch, deck, spin, history };
}
