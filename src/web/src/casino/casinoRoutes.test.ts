import { describe, expect, it } from "vitest";
import { CASINO_ROUTES } from "./casinoApi";
import { assertPlayMoneyCopy, formatDemoChips, formatPlayBalance, PLAY_LABEL, DEMO_CHIPS_LABEL } from "./currency";
import { buildingOps } from "@/enterprise-city/buildingOps";

describe("Sprint 16 casino routes and play-money copy", () => {
  it("exposes lobby, venue, and roulette deep links", () => {
    expect(CASINO_ROUTES.lobby).toBe("/casino");
    expect(CASINO_ROUTES.venue("odessa-prime")).toBe("/casino/venues/odessa-prime");
    expect(CASINO_ROUTES.roulette("odessa-prime")).toBe("/casino/venues/odessa-prime/roulette");
  });

  it("labels currency as PLAY or DEMO CHIPS only", () => {
    const copy = `${formatPlayBalance(10000)} ${formatDemoChips(25)} ${PLAY_LABEL} ${DEMO_CHIPS_LABEL}`;
    expect(copy).toContain("PLAY");
    expect(copy).toContain("DEMO CHIPS");
    expect(assertPlayMoneyCopy(copy)).toBe(true);
    expect(assertPlayMoneyCopy("$100")).toBe(false);
    expect(assertPlayMoneyCopy("100 €")).toBe(false);
    expect(assertPlayMoneyCopy("100 ₽")).toBe(false);
  });

  it("binds City enter action to the casino lobby", () => {
    const enter = buildingOps("casino").quickActions.find((a) => a.id === "open");
    expect(enter?.label).toBe("Войти в казино");
    expect(enter?.route).toBe("/casino");
  });
});
