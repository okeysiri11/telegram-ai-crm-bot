import { afterEach, describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
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
    expect(bar?.sublabel).toBe("ODESSA PRIME");
    expect(restaurant?.sublabel).toBe("ODESSA PRIME");
    expect(poker?.sublabel).toBe("ODESSA PRIME");
    expect((slots?.visuals ?? []).filter((v) => v.role === "machine")).toHaveLength(3);
    expect((slots?.visuals ?? []).filter((v) => v.role === "chair")).toHaveLength(3);
    expect(slots?.polygons).toHaveLength(6);
    expect((slots?.visuals ?? []).some((v) => v.role === "reflect")).toBe(false);
    expect(slots?.objects).toEqual([
      "machine-1",
      "machine-2",
      "machine-3",
      "chair-1",
      "chair-2",
      "chair-3",
    ]);
    expect((roulette?.visuals ?? []).some((v) => v.role === "sign")).toBe(true);
    expect((roulette?.visuals ?? []).some((v) => v.role === "lamp")).toBe(true);
    expect(bar?.objects).toEqual(expect.arrayContaining(["sign", "shelves", "bottles"]));
    expect(restaurant?.objects).toEqual(expect.arrayContaining(["sign", "tables", "lamps"]));
    for (const zone of HALL_ZONES) {
      expect(zone.tooltip).toBeTruthy();
      expect(zone.visuals?.length).toBeGreaterThan(0);
      expect("polygon" in zone).toBe(false);
    }
  });

  it("renders the hall interior without permanent rectangle overlays", async () => {
    const view = mount("/casino/lobby");
    expect(await screen.findByTestId("casino-lobby", {}, { timeout: 8000 })).toBeTruthy();
    expect(screen.getByTestId("lobby-hall")).toBeTruthy();
    const stage = screen.getByTestId("lobby-hall-stage");
    const wrap = screen.getByTestId("hall-image-wrap");
    const overlay = screen.getByTestId("hall-spatial-overlay");
    const photo = view.container.querySelector(".op-lobby-photo");
    expect(stage.getAttribute("data-hall-full-width")).toBe("true");
    expect(stage.getAttribute("data-hall-fit")).toBe("contain");
    expect(wrap.contains(photo)).toBe(true);
    expect(wrap.contains(overlay)).toBe(true);
    expect(screen.getByTestId("hall-spatial-overlay").getAttribute("data-idle")).toBe("true");
    expect(screen.getByTestId("hall-spatial-overlay").getAttribute("data-active-zone")).toBe("");
    expect(screen.getByTestId("hall-lit-overlay").getAttribute("data-lit-zone")).toBe("");
    expect(screen.getByTestId("hall-lit-overlay").getAttribute("class")).not.toContain("is-on");
    expect(view.container.querySelector(".op-hall-lit.is-on")).toBeNull();
    expect(view.container.querySelector('[data-visual-on="true"]')).toBeNull();
    expect(view.container.querySelector(".op-hall-shape")).toBeNull();
    expect(view.container.querySelector("[data-testid='hall-visual-layer']")).toBeTruthy();
    expect(view.container.querySelectorAll(".op-hall-hit").length).toBeGreaterThan(0);
    expect(view.container.querySelectorAll("[data-testid='hall-zone-label']").length).toBe(0);
    expect(view.container.querySelectorAll(".op-hotspot").length).toBe(0);
    expect(screen.getByTestId("slots-photo-overlay").className).not.toContain("is-on");
    expect(screen.getByTestId("slots-photo-overlay").getAttribute("data-slots-hovered")).toBe("false");
    expect(screen.getByTestId("slots-photo-overlay").getAttribute("src")).toBe(
      "/assets/casino/lobby/hall-slots-gold-edge.png",
    );
    expect(screen.getByTestId("slots-chair-overlay").getAttribute("class")).not.toContain("is-on");
    expect(screen.getByTestId("slots-chair-overlay").querySelectorAll("ellipse, circle, polygon, rect")).toHaveLength(0);
    const idleChairPaths = screen.getByTestId("slots-chair-overlay").querySelectorAll("path");
    expect(idleChairPaths.length).toBeGreaterThan(0);
    idleChairPaths.forEach((path) => {
      expect(path.getAttribute("fill")).toBe("none");
      expect(path.getAttribute("d")?.toLowerCase()).not.toContain("z");
    });
    expect(screen.queryByTestId("slots-debug-mask")).toBeNull();
    expect(screen.queryByTestId("slots-mask-debug")).toBeNull();
    expect(view.container.querySelectorAll("[data-slot-object]").length).toBe(0);
    expect(screen.queryByTestId("hall-zone-label")).toBeNull();
    expect(screen.queryByText("ВОЙТИ В РУЛЕТКУ")).toBeNull();
    expect(screen.queryByTestId("hotspot-vip")).toBeNull();
    for (const zone of HALL_ZONES) {
      const hit = screen.getByTestId(`hotspot-${zone.id}`);
      expect(hit.getAttribute("aria-label")).toContain(zone.label);
    }
    view.unmount();
  }, 20000);

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
    expect(screen.getByTestId("hall-lit-overlay").getAttribute("data-lit-zone")).toBe("blackjack");
    expect(view.container.querySelector(".op-hall-mask.is-blackjack")).toBeTruthy();
    fireEvent.pointerLeave(screen.getByTestId("hotspot-blackjack"));
    expect(screen.queryByTestId("hall-zone-label")).toBeNull();
    view.unmount();
  });

  it("activates one slots hover state without painting slot polygons", () => {
    const view = mount("/casino/lobby");
    fireEvent.pointerEnter(screen.getByTestId("hotspot-slots"));
    const overlay = screen.getByTestId("hall-lit-overlay");
    expect(overlay.getAttribute("data-lit-zone")).toBe("slots");
    expect(screen.getByTestId("slots-photo-overlay").getAttribute("data-slots-hovered")).toBe("true");
    expect(screen.getByTestId("slots-chair-overlay").getAttribute("class")).toContain("is-on");
    expect(screen.getByTestId("slots-chair-overlay").querySelectorAll("ellipse, circle, polygon, rect")).toHaveLength(0);
    expect(view.container.querySelectorAll("[data-visual-on='true']")).toHaveLength(0);
    expect(view.container.querySelectorAll("[data-slot-object]")).toHaveLength(0);
    expect(view.container.querySelector(".op-hall-mask.is-slots")).toBeNull();
    expect(view.container.querySelector(".op-hall-slot-halo")).toBeNull();
    expect(screen.queryByTestId("slots-debug-mask")).toBeNull();
    expect(screen.queryByTestId("slots-mask-debug")).toBeNull();
    expect(screen.getByTestId("hall-zone-label").textContent).toContain("ИГРАТЬ В АВТОМАТЫ");
    fireEvent.pointerLeave(screen.getByTestId("hotspot-slots"));
    expect(screen.getByTestId("slots-photo-overlay").getAttribute("data-slots-hovered")).toBe("false");
    expect(screen.getByTestId("slots-photo-overlay").className).not.toContain("is-on");
    expect(screen.getByTestId("slots-chair-overlay").getAttribute("class")).not.toContain("is-on");
    expect(overlay.getAttribute("data-lit-zone")).toBe("");
    view.unmount();
  });

  it("matches focus to hover and activates with keyboard", async () => {
    const view = mount("/casino/lobby");
    const roulette = screen.getByTestId("hotspot-roulette");
    fireEvent.focus(roulette);
    expect(roulette.className).toContain("is-active");
    fireEvent.keyDown(roulette, { key: "Enter" });
    expect(await screen.findByTestId("roulette-table", {}, { timeout: 15000 })).toBeTruthy();
    expect(screen.getByText("← В ЗАЛ")).toBeTruthy();
    view.unmount();
  }, 30000);

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
    fireEvent.pointerEnter(screen.getByTestId("hotspot-roulette"));
    expect(view.container.querySelector(".op-hall-lit.is-on")).toBeTruthy();
    expect(screen.getByTestId("hall-lit-overlay").getAttribute("data-lit-zone")).toBe("roulette");
    fireEvent.pointerLeave(screen.getByTestId("hotspot-roulette"));
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

  it("activates only the hovered destination and clears on pointer leave", () => {
    const view = mount("/casino/lobby");
    const overlay = screen.getByTestId("hall-spatial-overlay");
    const stage = screen.getByTestId("lobby-hall-stage");
    for (const zone of HALL_ZONES) {
      fireEvent.pointerEnter(screen.getByTestId(`hotspot-${zone.id}`));
      expect(overlay.getAttribute("data-idle")).toBe("false");
      expect(overlay.getAttribute("data-active-zone")).toBe(zone.id);
      expect(stage.getAttribute("data-hall-active")).toBe(zone.id);
      expect(screen.getByTestId("hall-lit-overlay").getAttribute("data-lit-zone")).toBe(zone.id);
      if (zone.id === "slots") {
        expect(screen.getByTestId("slots-photo-overlay").getAttribute("data-slots-hovered")).toBe("true");
        expect(view.container.querySelector("[data-visual-on='true']")).toBeNull();
      } else {
        const lit = [...view.container.querySelectorAll("[data-visual-on='true']")];
        expect(lit.length).toBeGreaterThan(0);
        expect(lit.every((el) => el.getAttribute("data-visual-zone") === zone.id)).toBe(true);
      }
      expect(screen.getAllByTestId("hall-zone-label")).toHaveLength(1);
      expect(screen.getByTestId("hall-zone-label").getAttribute("data-tooltip-zone")).toBe(zone.id);
      fireEvent.pointerLeave(screen.getByTestId(`hotspot-${zone.id}`));
      expect(overlay.getAttribute("data-idle")).toBe("true");
      expect(overlay.getAttribute("data-active-zone")).toBe("");
      expect(screen.getByTestId("hall-lit-overlay").getAttribute("data-lit-zone")).toBe("");
      expect(view.container.querySelector("[data-visual-on='true']")).toBeNull();
      expect(screen.queryByTestId("hall-zone-label")).toBeNull();
    }
    view.unmount();
  });

  it("keeps a single active zone when focus moves between destinations", () => {
    const view = mount("/casino/lobby");
    fireEvent.pointerEnter(screen.getByTestId("hotspot-roulette"));
    fireEvent.focus(screen.getByTestId("hotspot-slots"));
    expect(screen.getByTestId("hall-spatial-overlay").getAttribute("data-active-zone")).toBe("slots");
    expect(screen.getByTestId("hall-lit-overlay").getAttribute("data-lit-zone")).toBe("slots");
    expect(view.container.querySelector("[data-visual-zone='roulette'][data-visual-on='true']")).toBeNull();
    expect(screen.getByTestId("slots-photo-overlay").getAttribute("data-slots-hovered")).toBe("true");
    expect(view.container.querySelector(".op-hall-mask.is-slots")).toBeNull();
    expect(view.container.querySelectorAll("[data-slot-object]")).toHaveLength(0);
    expect(view.container.querySelector(".op-hall-mask.is-reflect")).toBeNull();
    expect(screen.getAllByTestId("hall-zone-label")).toHaveLength(1);
    expect(screen.getByTestId("hall-zone-label").textContent).toContain("ИГРАТЬ В АВТОМАТЫ");
    fireEvent.blur(screen.getByTestId("hotspot-slots"));
    expect(screen.getByTestId("hall-spatial-overlay").getAttribute("data-idle")).toBe("true");
    view.unmount();
  });

  it("navigates with Space and shows polished destination copy", async () => {
    const view = mount("/casino/lobby");
    fireEvent.pointerEnter(screen.getByTestId("hotspot-bar"));
    expect(screen.getByTestId("hall-zone-label").textContent).toContain("БАР");
    expect(screen.getByTestId("hall-zone-label").textContent).toContain("ODESSA PRIME");
    fireEvent.pointerLeave(screen.getByTestId("hotspot-bar"));
    fireEvent.pointerEnter(screen.getByTestId("hotspot-restaurant"));
    expect(screen.getByTestId("hall-zone-label").textContent).toContain("РЕСТОРАН");
    expect(screen.getByTestId("hall-zone-label").textContent).toContain("ODESSA PRIME");
    fireEvent.pointerLeave(screen.getByTestId("hotspot-restaurant"));
    const poker = screen.getByTestId("hotspot-poker");
    fireEvent.focus(poker);
    fireEvent.keyDown(poker, { key: " " });
    expect(await screen.findByTestId("poker-room", {}, { timeout: 8000 })).toBeTruthy();
    expect(screen.getByText("← В ЗАЛ")).toBeTruthy();
    view.unmount();
  }, 20000);
});
