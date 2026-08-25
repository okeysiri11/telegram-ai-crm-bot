import { describe, expect, it } from "vitest";
import { CASINO_ROUTES } from "./casinoApi";

describe("Sprint 15 casino routes", () => {
  it("exposes lobby, venue, and roulette deep links", () => {
    expect(CASINO_ROUTES.lobby).toBe("/casino");
    expect(CASINO_ROUTES.venue("odessa-prime")).toBe("/casino/venues/odessa-prime");
    expect(CASINO_ROUTES.roulette("odessa-prime")).toBe("/casino/venues/odessa-prime/roulette");
  });
});
