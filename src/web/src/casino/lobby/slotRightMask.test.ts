import { describe, expect, it } from "vitest";
import { HALL_ART } from "./hallZones";
import { DEBUG_SLOT_MASK, SLOTS_GOLD_EDGE, SLOTS_MASK, slotsMaskReady } from "./slotRightMask";

describe("slots group photo mask contract", () => {
  it("keeps the debug magenta tint off by default", () => {
    expect(DEBUG_SLOT_MASK).toBe(false);
  });

  it("normalizes the mask to the hall photograph", () => {
    expect(SLOTS_MASK.src).toBe("/assets/casino/lobby/hall-slots-foreground.png");
    expect(SLOTS_GOLD_EDGE.src).toBe("/assets/casino/lobby/hall-slots-gold-edge.png");
    expect(SLOTS_MASK.width).toBe(HALL_ART.width);
    expect(SLOTS_MASK.height).toBe(HALL_ART.height);
    expect(SLOTS_GOLD_EDGE.width).toBe(HALL_ART.width);
    expect(SLOTS_GOLD_EDGE.height).toBe(HALL_ART.height);
    expect(SLOTS_MASK.width).toBe(1600);
    expect(SLOTS_MASK.height).toBe(1066);
    expect(slotsMaskReady()).toBe(true);
  });
});
