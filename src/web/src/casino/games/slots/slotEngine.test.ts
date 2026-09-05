import { describe, expect, it } from "vitest";
import { SLOT_CATALOG, filterSlotCatalog, getSlotDefinition } from "./slotCatalog";
import { createSlotRng, evaluateSlotGrid, resolveSlotSpin } from "./slotEngine";

describe("Odessa Prime slot engine", () => {
  it("exposes six distinct catalog machines", () => {
    expect(SLOT_CATALOG).toHaveLength(6);
    const titles = SLOT_CATALOG.map((item) => item.title);
    expect(new Set(titles).size).toBe(6);
    expect(titles).toContain("Olympus Crown");
    expect(getSlotDefinition("candy-fortune")?.theme).toBe("candy");
  });

  it("filters catalog locally for future provider expansion", () => {
    expect(filterSlotCatalog("pharaoh", "all")[0]?.id).toBe("pharaohs-book");
    expect(filterSlotCatalog("", "classic").every((item) => item.tags.includes("classic"))).toBe(true);
    expect(SLOT_CATALOG.every((item) => item.demoAvailable && !item.realAvailable && item.providerId)).toBe(true);
  });

  it("deducts one bet and credits one win from the resolved grid", () => {
    const def = getSlotDefinition("olympus-crown")!;
    const grid = [
      ["ZEUS", "OWL", "URN"],
      ["ZEUS", "OWL", "LAUREL"],
      ["ZEUS", "BOLT", "URN"],
      ["CROWN", "OWL", "LAUREL"],
      ["CROWN", "OWL", "URN"],
    ];
    const win = evaluateSlotGrid(def, grid, 10);
    expect(win).toBeGreaterThan(0);
    const lossGrid = [
      ["ZEUS", "OWL", "URN"],
      ["CROWN", "BOLT", "LAUREL"],
      ["OWL", "URN", "BOLT"],
      ["LAUREL", "CROWN", "OWL"],
      ["BOLT", "LAUREL", "CROWN"],
    ];
    expect(evaluateSlotGrid(def, lossGrid, 10)).toBe(0);
  });

  it("is deterministic for a seeded RNG", () => {
    const def = getSlotDefinition("big-catch")!;
    const a = resolveSlotSpin(def, 25, createSlotRng(42));
    const b = resolveSlotSpin(def, 25, createSlotRng(42));
    expect(a.grid).toEqual(b.grid);
    expect(a.win).toBe(b.win);
    expect(a.bet).toBe(25);
  });
});
