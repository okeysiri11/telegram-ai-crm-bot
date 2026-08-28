import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { CASINO_ROUTES } from "./casinoApi";
import { assertPlayMoneyCopy, formatDemoChips, formatPlayBalance, PLAY_LABEL, DEMO_CHIPS_LABEL } from "./currency";
import { buildingOps } from "@/enterprise-city/buildingOps";
import { sanitizeReturnTo, resolvePostLoginPath, loginRedirect } from "@/navigation/safeReturnTo";
import { EUROPEAN_ORDER } from "./RouletteWheel";
import { CasinoFloorPage } from "./CasinoFloorPage";
import { CasinoTableBrowserPage } from "./CasinoTableBrowserPage";

describe("Sprint 17 Odessa Prime casino", () => {
  it("exposes immersive casino routes", () => {
    expect(CASINO_ROUTES.lobby).toBe("/casino");
    expect(CASINO_ROUTES.floor).toBe("/casino/floor");
    expect(CASINO_ROUTES.tables).toBe("/casino/roulette");
    expect(CASINO_ROUTES.table("roulette-royale-1")).toBe("/casino/roulette/royale-1");
    expect(CASINO_ROUTES.venue("odessa-prime")).toBe("/casino/venues/odessa-prime");
  });

  it("keeps PLAY / DEMO CHIPS copy", () => {
    const copy = `${formatPlayBalance(10000)} ${formatDemoChips(25)} ${PLAY_LABEL} ${DEMO_CHIPS_LABEL}`;
    expect(assertPlayMoneyCopy(copy)).toBe(true);
    expect(assertPlayMoneyCopy("$")).toBe(false);
  });

  it("binds city enter to casino entrance", () => {
    expect(buildingOps("casino").quickActions[0]?.label).toBe("Войти в казино");
    expect(buildingOps("casino").quickActions[0]?.route).toBe("/casino");
  });

  it("sanitizes returnTo and rejects open redirects", () => {
    expect(sanitizeReturnTo("/casino/roulette/roulette-royale-1")).toBe("/casino/roulette/roulette-royale-1");
    expect(sanitizeReturnTo("/enterprise-city?building=casino")).toBe("/enterprise-city?building=casino");
    expect(sanitizeReturnTo("https://evil.example/phish")).toBeNull();
    expect(sanitizeReturnTo("//evil.example")).toBeNull();
    expect(sanitizeReturnTo("javascript:alert(1)")).toBeNull();
    expect(sanitizeReturnTo("/login")).toBeNull();
    expect(loginRedirect("/casino/floor")).toContain("returnTo=");
    expect(
      resolvePostLoginPath({
        queryReturnTo: "/casino/roulette/roulette-royale-1",
        stateFrom: "/dashboard",
        roleHome: "/dashboard",
      }),
    ).toBe("/casino/roulette/roulette-royale-1");
  });

  it("renders casino floor zones and map toggle", () => {
    render(
      <MemoryRouter>
        <CasinoFloorPage />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("hotspot-roulette").getAttribute("aria-label")).toContain("РУЛЕТКА");
    expect(screen.getByText("ЗАЛ")).toBeTruthy();
    expect(screen.getByText("КАРТА")).toBeTruthy();
  });

  it("renders roulette table browser labels", () => {
    render(
      <MemoryRouter>
        <CasinoTableBrowserPage />
      </MemoryRouter>,
    );
    expect(screen.getByText("Roulette Royale 1")).toBeTruthy();
    expect(screen.getByText("Roulette Monaco")).toBeTruthy();
  });

  it("uses a 37-pocket European wheel order", () => {
    expect(EUROPEAN_ORDER).toHaveLength(37);
    expect(new Set(EUROPEAN_ORDER).size).toBe(37);
  });
});
