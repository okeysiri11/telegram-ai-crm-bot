// AUTO-GENERATED — Phase 4.4A photoreal cutouts (chroma-keyed from approved renders).
// Per-machine screen overlay rects, measured from the processed PNG alpha + dark bezel.
// Variant fallbacks remain for any catalog entry without a per-id override.
export const CABINET_SCREEN_RECT: Record<"curved" | "square" | "slim", { leftPct: number; topPct: number; widthPct: number; heightPct: number }> = {
  curved: { leftPct: 16.719, topPct: 20.865, widthPct: 68.438, heightPct: 38.903 },
  slim: { leftPct: 21.63, topPct: 29.491, widthPct: 55.543, heightPct: 30.796 },
  square: { leftPct: 22.5, topPct: 32.132, widthPct: 55.333, heightPct: 28.328 },
};

export const CABINET_ASPECT: Record<"curved" | "square" | "slim", { w: number; h: number }> = {
  curved: { w: 640, h: 1203 },
  slim: { w: 460, h: 898 },
  square: { w: 600, h: 1059 },
};

export const CABINET_SCREEN_RECT_BY_ID: Record<string, { leftPct: number; topPct: number; widthPct: number; heightPct: number }> = {
  "olympus-crown": { leftPct: 16.719, topPct: 20.865, widthPct: 68.438, heightPct: 38.903 },
  "lady-emerald": { leftPct: 26.406, topPct: 31.349, widthPct: 47.188, heightPct: 29.023 },
  "pharaohs-book": { leftPct: 22.5, topPct: 33.239, widthPct: 55.0, heightPct: 27.29 },
  "buffalo-fortune": { leftPct: 22.5, topPct: 31.024, widthPct: 55.667, heightPct: 29.366 },
  "candy-fortune": { leftPct: 21.087, topPct: 31.292, widthPct: 54.348, heightPct: 29.065 },
  "big-catch": { leftPct: 22.174, topPct: 27.69, widthPct: 56.739, heightPct: 32.527 },
};

export const CABINET_ASPECT_BY_ID: Record<string, { w: number; h: number }> = {
  "olympus-crown": { w: 640, h: 1203 },
  "lady-emerald": { w: 640, h: 1075 },
  "pharaohs-book": { w: 600, h: 1059 },
  "buffalo-fortune": { w: 600, h: 1025 },
  "candy-fortune": { w: 460, h: 898 },
  "big-catch": { w: 460, h: 827 },
};
