import { afterEach, describe, expect, it } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CasinoApp } from "./CasinoApp";
import { CasinoBrowseRoute } from "@/shell/CasinoBrowseRoute";
import { casinoSound } from "./casinoSound";
import { HALL_ENTER_MS, HALL_ZONES, validateHallZones } from "./lobby/hallZones";
import { CASINO_ROUTES } from "./state/casinoRoutes";

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/casino/*"
          element={
            <CasinoBrowseRoute>
              <CasinoApp />
            </CasinoBrowseRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

function mockReducedMotion(enabled: boolean) {
  const original = window.matchMedia;
  window.matchMedia = ((query: string) =>
    ({
      matches: enabled && String(query).includes("prefers-reduced-motion"),
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    })) as typeof window.matchMedia;
  return () => {
    window.matchMedia = original;
  };
}

describe("Odessa Prime interactive hall", () => {
  afterEach(() => {
    casinoSound.setMuted(true);
  });

  it("validates six unique spatial zones with normalized polygons", () => {
    expect(HALL_ZONES).toHaveLength(6);
    expect(HALL_ZONES.map((z) => z.id)).toEqual([
      "roulette",
      "blackjack",
      "poker",
      "restaurant",
      "bar",
      "slots",
    ]);
    expect(validateHallZones()).toEqual([]);
    const roulette = HALL_ZONES.find((z) => z.id === "roulette");
    const blackjack = HALL_ZONES.find((z) => z.id === "blackjack");
    const poker = HALL_ZONES.find((z) => z.id === "poker");
    const slots = HALL_ZONES.find((z) => z.id === "slots");
    const bar = HALL_ZONES.find((z) => z.id === "bar");
    const restaurant = HALL_ZONES.find((z) => z.id === "restaurant");
    expect(roulette?.route).toBe("/casino/roulette/royale-1");
    expect(blackjack?.route).toBe("/casino/blackjack");
    expect(poker?.route).toBe("/casino/poker");
    expect(slots?.route).toBe("/casino/slots");
    expect(bar?.route).toBe("/casino/bar");
    expect(restaurant?.route).toBe("/casino/restaurant");
    expect(roulette?.polygons.length).toBeGreaterThanOrEqual(2);
    expect(slots?.polygons.length).toBeGreaterThanOrEqual(3);
    expect(blackjack?.objects.length).toBeGreaterThanOrEqual(1);
    expect(poker?.objects).toContain("doorway");
    expect(bar?.objects).toContain("shelves");
    expect(restaurant?.objects).toContain("tables");
    for (const zone of HALL_ZONES) {
      expect(zone.tooltip).toBeTruthy();
      expect("polygon" in zone).toBe(false);
    }
  });

  it("renders the hall interior without permanent rectangle overlays", async () => {
    const view = mount("/casino/lobby");
    await waitFor(() => expect(screen.getByTestId("casino-lobby")).toBeTruthy());
    expect(screen.getByTestId("lobby-hall")).toBeTruthy();
    const stage = screen.getByTestId("lobby-hall-stage");
    const wrap = screen.getByTestId("hall-image-wrap");
    const overlay = screen.getByTestId("hall-spatial-overlay");
    const photo = view.container.querySelector(".op-lobby-photo");
    expect(stage.getAttribute("data-hall-full-width")).toBe("true");
    expect(stage.getAttribute("data-hall-fit")).toBe("contain");
    expect(wrap.contains(photo)).toBe(true);
    expect(wrap.contains(overlay)).toBe(true);
    expect(view.container.querySelector(".op-hall-shape.is-on")).toBeNull();
    expect(view.container.querySelector("[data-testid='hall-visual-layer']")).toBeTruthy();
    expect(view.container.querySelectorAll(".op-hall-hit").length).toBeGreaterThan(0);
    expect(view.container.querySelectorAll("[data-testid='hall-zone-label']").length).toBe(0);
    expect(view.container.querySelectorAll(".op-hotspot").length).toBe(0);
    expect(screen.queryByTestId("hall-zone-label")).toBeNull();
    expect(screen.queryByText("ВОЙТИ В РУЛЕТКУ")).toBeNull();
    expect(screen.queryByTestId("hotspot-vip")).toBeNull();
    for (const zone of HALL_ZONES) {
      const hit = screen.getByTestId(`hotspot-${zone.id}`);
      expect(hit.getAttribute("aria-label")).toContain(zone.label);
    }
    view.unmount();
  });

  it("shows a contextual label only while a zone is active", () => {
    const view = mount("/casino/lobby");
    const roulette = screen.getByTestId("hotspot-roulette");
    fireEvent.pointerEnter(roulette);
    expect(roulette.className).toContain("is-active");
    expect(screen.getByTestId("hall-zone-label").textContent).toContain("РУЛЕТКА");
    expect(screen.getByTestId("hall-zone-label").textContent).toContain("MONTE CARLO");
    expect(screen.getByTestId("hall-zone-label").getAttribute("data-tooltip-zone")).toBe("roulette");
    expect(screen.getAllByTestId("hall-zone-label")).toHaveLength(1);
    expect(screen.getByTestId("lobby-hall-stage").className).toContain("is-focused");
    fireEvent.pointerLeave(roulette);
    fireEvent.pointerEnter(screen.getByTestId("hotspot-blackjack"));
    expect(screen.getByTestId("hall-zone-label").textContent).toContain("BLACKJACK");
    expect(screen.getByTestId("hall-zone-label").getAttribute("data-tooltip-zone")).toBe("blackjack");
    expect(view.container.querySelector(".op-hall-shape.is-blackjack.is-on")).toBeTruthy();
    fireEvent.pointerLeave(screen.getByTestId("hotspot-blackjack"));
    expect(screen.queryByTestId("hall-zone-label")).toBeNull();
    view.unmount();
  });

  it("matches focus to hover and activates with keyboard", async () => {
    const view = mount("/casino/lobby");
    const roulette = screen.getByTestId("hotspot-roulette");
    fireEvent.focus(roulette);
    expect(roulette.className).toContain("is-active");
    fireEvent.keyDown(roulette, { key: "Enter" });
    expect(await screen.findByTestId("roulette-table", {}, { timeout: 8000 })).toBeTruthy();
    expect(screen.getByText("← В ЗАЛ")).toBeTruthy();
    view.unmount();
  }, 20000);

  it("navigates each spatial zone to its existing room", async () => {
    const cases = [
      ["roulette", "roulette-table"],
      ["blackjack", "blackjack-table"],
      ["poker", "poker-room"],
      ["slots", "slots-room"],
      ["bar", "bar-room"],
      ["restaurant", "restaurant-room"],
    ] as const;
    for (const [id, testid] of cases) {
      const view = mount("/casino/lobby");
      fireEvent.click(screen.getByTestId(`hotspot-${id}`));
      expect(await screen.findByTestId(testid, {}, { timeout: 8000 })).toBeTruthy();
      expect(screen.getByText("← В ЗАЛ")).toBeTruthy();
      view.unmount();
    }
  }, 60000);

  it("skips the click zoom when prefers-reduced-motion is set", async () => {
    const restore = mockReducedMotion(true);
    const view = mount("/casino/lobby");
    fireEvent.click(screen.getByTestId("hotspot-blackjack"));
    expect(await screen.findByTestId("blackjack-table", {}, { timeout: 8000 })).toBeTruthy();
    view.unmount();
    restore();
  }, 20000);

  it("keeps debug outlines behind a development-only query", () => {
    const hidden = mount("/casino/lobby");
    expect(hidden.container.querySelector(".op-hall-glow.is-debug")).toBeNull();
    expect(hidden.container.querySelector(".op-hall-debug-id")).toBeNull();
    hidden.unmount();
    const shown = mount("/casino/lobby?casinoHotspots=debug");
    expect(shown.container.querySelector(".op-hall-glow.is-debug")).toBeTruthy();
    expect(shown.container.querySelector(".op-hall-debug-id")?.textContent).toBe("roulette");
    shown.unmount();
  });

  it("does not track pointer coordinates in React state", () => {
    const view = mount("/casino/lobby");
    const stage = screen.getByTestId("lobby-hall-stage");
    fireEvent.pointerMove(stage, { clientX: 10, clientY: 10 });
    fireEvent.pointerMove(stage, { clientX: 80, clientY: 80 });
    expect(stage.getAttribute("data-hall-active")).toBe("");
    expect(screen.queryByTestId("hall-zone-label")).toBeNull();
    fireEvent.pointerEnter(screen.getByTestId("hotspot-roulette"));
    expect(stage.getAttribute("data-hall-active")).toBe("roulette");
    view.unmount();
  });

  it("keeps overlay bounds on the hall image and one tooltip per zone", () => {
    const view = mount("/casino/lobby");
    const wrap = screen.getByTestId("hall-image-wrap");
    expect(wrap.querySelector("img.op-hall-art")?.getAttribute("width")).toBe("1600");
    expect(wrap.querySelector("img.op-hall-art")?.getAttribute("height")).toBe("1066");
    expect(screen.getByTestId("hall-spatial-overlay").parentElement).toBe(wrap);
    expect(HALL_ENTER_MS).toBeGreaterThanOrEqual(150);
    expect(HALL_ENTER_MS).toBeLessThanOrEqual(300);
    expect(CASINO_ROUTES.lobby).toBe("/casino");
    expect(CASINO_ROUTES.lobbyAlias).toBe("/casino/lobby");
    expect(CASINO_ROUTES.rouletteLive).toBe("/casino/roulette/royale-1");
    fireEvent.pointerEnter(screen.getByTestId("hotspot-slots"));
    expect(screen.getAllByTestId("hall-zone-label")).toHaveLength(1);
    fireEvent.pointerEnter(screen.getByTestId("hotspot-bar"));
    expect(screen.getAllByTestId("hall-zone-label")).toHaveLength(1);
    expect(screen.getByTestId("hall-zone-label").getAttribute("data-tooltip-zone")).toBe("bar");
    view.unmount();
  });
});
