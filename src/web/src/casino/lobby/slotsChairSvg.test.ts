import { describe, expect, it } from "vitest";
import { HALL_ART } from "./hallZones";
import { chairPathClosed, SLOTS_CHAIR_GROUPS } from "./SlotsChairSvg";

describe("slots chair SVG open paths", () => {
  it("keeps three independent chair groups in hall coordinates", () => {
    expect(SLOTS_CHAIR_GROUPS.map((g) => g.id)).toEqual(["slot-chair-1", "slot-chair-2", "slot-chair-3"]);
    expect(HALL_ART.width).toBe(1600);
    expect(HALL_ART.height).toBe(1066);
  });

  it("uses only open unfilled strokes and no cloned path", () => {
    const ds = SLOTS_CHAIR_GROUPS.flatMap((g) => g.paths.map((p) => p.d));
    expect(ds.length).toBeGreaterThan(0);
    expect(new Set(ds).size).toBe(ds.length);
    for (const d of ds) {
      expect(chairPathClosed(d)).toBe(false);
      expect(d).not.toMatch(/[Aa]/);
      expect(d.toLowerCase()).not.toContain("z");
    }
  });
});
