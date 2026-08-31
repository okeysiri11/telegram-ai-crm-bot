import { describe, expect, it } from "vitest";
import { HALL_ART } from "./hallZones";
import { ROULETTE_GOLD_GROUPS, roulettePathClosed } from "./RouletteGoldSvg";

describe("roulette gold SVG open paths", () => {
  it("keeps sign, lamp, wheel, table, and chair groups in hall coordinates", () => {
    expect(ROULETTE_GOLD_GROUPS.map((g) => g.id)).toEqual([
      "roulette-sign",
      "roulette-lamp",
      "roulette-wheel",
      "roulette-table",
      "roulette-chair",
    ]);
    expect(HALL_ART.width).toBe(1600);
    expect(HALL_ART.height).toBe(1066);
  });

  it("uses only open unfilled strokes and no ellipses or closed silhouettes", () => {
    const ds = ROULETTE_GOLD_GROUPS.flatMap((g) => g.paths.map((p) => p.d));
    expect(ds.length).toBeGreaterThan(0);
    expect(new Set(ds).size).toBe(ds.length);
    for (const d of ds) {
      expect(roulettePathClosed(d)).toBe(false);
      expect(d).not.toMatch(/[Aa]/);
      expect(d.toLowerCase()).not.toContain("z");
    }
  });
});
