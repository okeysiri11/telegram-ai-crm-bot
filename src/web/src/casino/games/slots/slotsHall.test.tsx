/**
 * Phase 4.0 — Slots Room hall, catalog, demo engine, navigation.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { CasinoApp } from "../../CasinoApp";
import { CasinoBrowseRoute } from "@/shell/CasinoBrowseRoute";
import { useAuthStore } from "@/auth/authStore";
import { SLOT_CATALOG } from "./slotCatalog";
import { SlotGameScreen } from "./SlotGameScreen";
import { cabinetScreenRect } from "./cabinetAssets";
import {
  cabinetPlayLayout,
  overlayContainedIn,
  overlayWithinUnitSquare,
  seatedCrop,
} from "./cabinetPlayGeometry";
import { RouletteHall } from "../../rooms/RouletteHall";
import { BlackjackSalon } from "../../rooms/BlackjackSalon";
import { PokerRoom } from "../../rooms/PokerRoom";

function mount(path: string, entries?: string[]) {
  return render(
    <MemoryRouter initialEntries={entries || [path]}>
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

describe("Phase 4.0 Slots Hall", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.useRealTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("opens the slots hall from the casino lobby hotspot", async () => {
    const view = mount("/casino/lobby");
    fireEvent.click(await screen.findByTestId("hotspot-slots"));
    expect(await screen.findByTestId("slots-room", {}, { timeout: 8000 })).toBeTruthy();
    view.unmount();
  }, 20000);

  it("renders six distinct machines and no bottom poker cycle", async () => {
    mount("/casino/slots");
    expect(await screen.findByTestId("slots-catalog")).toBeTruthy();
    for (const item of SLOT_CATALOG) {
      expect(screen.getByTestId(`slot-cabinet-${item.id}`)).toBeTruthy();
      expect(screen.getByTestId(`slot-play-${item.id}`).getAttribute("href")).toBe(`/casino/slots/${item.slug}`);
    }
    expect(screen.queryByText(/ДАЛЕЕ · ПОКЕР/)).toBeNull();
    expect(screen.getByTestId("slots-room").className).toContain("op-slots-hall");
    expect(screen.getByTestId("slots-search")).toBeTruthy();
    expect(screen.getByTestId("slots-filters").textContent).toMatch(/Classic/);
    expect(screen.getByTestId("slots-room").querySelector(".op-slots-env")).toBeTruthy();
    expect(screen.getByTestId("slots-room").querySelectorAll(".op-phys-cab")).toHaveLength(6);
    expect(new Set([...screen.getByTestId("slots-catalog").querySelectorAll("[data-variant]")].map((n) => n.getAttribute("data-variant"))).size).toBe(3);
    expect(screen.getByTestId("slots-catalog").querySelector(".op-cta")).toBeNull();
    for (const item of SLOT_CATALOG) {
      expect(screen.getByTestId(`slot-topper-${item.id}`)).toBeTruthy();
      expect(screen.getByTestId(`slot-reels-${item.id}`).textContent?.length).toBeGreaterThan(0);
      expect(screen.getByTestId(`slot-controls-${item.id}`).textContent).toMatch(/SPIN/);
      expect(screen.getByTestId(`slot-chair-${item.id}`)).toBeTruthy();
    }
    expect(screen.getByTestId("slots-room").querySelector(".op-slots-floor")).toBeTruthy();
  }, 20000);

  it("Phase 4.3: every cabinet is a baked image with a positioned live screen overlay, not a CSS shell", async () => {
    mount("/casino/slots");
    await screen.findByTestId("slots-catalog");
    expect(screen.getByTestId("slots-room").querySelector(".op-slots-env-bg")).toBeTruthy();
    for (const item of SLOT_CATALOG) {
      const asset = screen.getByTestId(`slot-cabinet-asset-${item.id}`) as HTMLImageElement;
      expect(asset.tagName).toBe("IMG");
      expect(asset.getAttribute("src")).toBe(`/assets/casino/slots/cabinets/${item.id}.png`);

      const screenEl = screen.getByTestId(`slot-preview-${item.id}`) as HTMLElement;
      expect(screenEl.style.left).toMatch(/%/);
      expect(screenEl.style.top).toMatch(/%/);
      expect(screenEl.style.width).toMatch(/%/);
      expect(screenEl.style.height).toMatch(/%/);

      const cab = screen.getByTestId(`slot-cabinet-${item.id}`) as HTMLElement;
      expect(cab.style.getPropertyValue("aspect-ratio")).not.toBe("");
      expect(screen.getByTestId(`slot-play-${item.id}`).getAttribute("aria-label")).toContain(item.title);
    }
  });

  it("Phase 4.3: selecting a cabinet flags it is-selected before the route change fires", async () => {
    vi.useFakeTimers();
    const view = render(
      <MemoryRouter initialEntries={["/casino/slots"]}>
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
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    fireEvent.click(screen.getByTestId("slot-play-olympus-crown"));
    expect(screen.getByTestId("slot-cabinet-olympus-crown").className).toContain("is-selected");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(250);
    });
    view.unmount();
    vi.useRealTimers();
  });

  it("Phase 4.4A: photoreal hall, six chairs, and Odessa Prime identity", async () => {
    mount("/casino/slots");
    await screen.findByTestId("slots-catalog");
    const bg = screen.getByTestId("slots-room").querySelector(".op-slots-env-bg") as HTMLImageElement;
    expect(bg.getAttribute("src")).toBe("/assets/casino/slots/hall-bg.jpg");
    expect(screen.getByTestId("slots-room").textContent).toMatch(/ODESSA PRIME CASINO/);
    expect(screen.getByTestId("slots-room").querySelectorAll(".op-phys-cab")).toHaveLength(6);
    for (const item of SLOT_CATALOG) {
      const chair = screen.getByTestId(`slot-chair-${item.id}`).querySelector("img") as HTMLImageElement;
      expect(chair.getAttribute("src")).toBe("/assets/casino/slots/chair.png");
      expect(screen.getByTestId(`slot-reels-${item.id}`).textContent?.length).toBeGreaterThan(0);
    }
  }, 20000);

  it("Phase 4.3: the hall renders without crashing under a narrow (mobile) viewport", async () => {
    const original = window.innerWidth;
    Object.defineProperty(window, "innerWidth", { writable: true, configurable: true, value: 375 });
    window.dispatchEvent(new Event("resize"));
    const view = mount("/casino/slots");
    expect(await screen.findByTestId("slots-catalog")).toBeTruthy();
    expect(screen.getByTestId("slots-room").querySelectorAll(".op-phys-cab")).toHaveLength(6);
    view.unmount();
    Object.defineProperty(window, "innerWidth", { writable: true, configurable: true, value: original });
  });

  it("locks the hall to a single desktop viewport in CSS", () => {
    const css = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "slotsHall.css"), "utf8");
    expect(css).toMatch(/overflow:\s*hidden/);
    expect(css).toMatch(/100dvh - 4\.2rem/);
    expect(css).toMatch(/op-phys-cab/);
    expect(css).toMatch(/op-phys-topper/);
    expect(css).toMatch(/op-phys-panel/);
    expect(css).toMatch(/op-phys-stool/);
    expect(css).toMatch(/op-slots-floor/);
    expect(css).toMatch(/prefers-reduced-motion/);
    expect(css).not.toMatch(/turquoise/);
  });

  it("opens a selected machine into a cabinet demo, then returns to the hall", async () => {
    const view = mount("/casino/slots");
    fireEvent.click(await screen.findByTestId("slot-play-olympus-crown"));
    expect(await screen.findByTestId("slot-game-screen", {}, { timeout: 8000 })).toBeTruthy();
    expect(screen.getByTestId("slot-demo-badge").textContent).toMatch(/Демо/);
    expect(screen.getByTestId("slot-game-screen").getAttribute("data-machine")).toBe("olympus-crown");
    fireEvent.click(screen.getByTestId("slot-back-room"));
    expect(await screen.findByTestId("slots-room", {}, { timeout: 8000 })).toBeTruthy();
    view.unmount();
  }, 20000);

  it("deducts bet once, credits win once, and locks spin while spinning", async () => {
    vi.useFakeTimers();
    const view = render(
      <MemoryRouter initialEntries={["/casino/slots/olympus-crown"]}>
        <Routes>
          <Route path="/casino/slots/:machineId" element={<SlotGameScreen />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByTestId("slot-game-screen")).toBeTruthy();
    const start = Number(screen.getByTestId("slot-demo-balance").textContent);
    expect(start).toBe(10_000);
    fireEvent.click(screen.getByTestId("slot-spin"));
    expect((screen.getByTestId("slot-spin") as HTMLButtonElement).disabled).toBe(true);
    expect(Number(screen.getByTestId("slot-demo-balance").textContent)).toBe(start - 10);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1300);
    });
    expect((screen.getByTestId("slot-spin") as HTMLButtonElement).disabled).toBe(false);
    const after = Number(screen.getByTestId("slot-demo-balance").textContent);
    const win = Number(screen.getByTestId("slot-demo-win").textContent);
    expect(after).toBe(start - 10 + win);
    fireEvent.click(screen.getByTestId("slot-history-toggle"));
    expect(screen.getByTestId("slot-history").textContent).toMatch(/Olympus Crown/);
    view.unmount();
  });

  it("lets a guest browse and play demo without a login modal", async () => {
    useAuthStore.setState({ accessToken: null, user: null });
    mount("/casino/slots/candy-fortune");
    expect(await screen.findByTestId("slot-game-screen")).toBeTruthy();
    expect(screen.queryByText(/ВОЙТИ/)).toBeNull();
    fireEvent.click(screen.getByTestId("slot-spin"));
    expect(screen.queryByText(/ВОЙТИ/)).toBeNull();
  }, 20000);

  it("keeps an authenticated session while moving hall → slots → machine → slots", async () => {
    useAuthStore.setState({
      accessToken: "aaa.bbb.ccc",
      user: { id: "1", email: "owner@demo.corp", name: "Owner", tenantId: "ados", roleId: "platform_owner", roles: ["owner"], permissions: [] },
    });
    const view = mount("/casino/lobby");
    fireEvent.click(await screen.findByTestId("hotspot-slots"));
    fireEvent.click(await screen.findByTestId("slot-play-lady-emerald", {}, { timeout: 8000 }));
    expect(await screen.findByTestId("slot-game-screen", {}, { timeout: 8000 })).toBeTruthy();
    expect(useAuthStore.getState().accessToken).toBe("aaa.bbb.ccc");
    fireEvent.click(screen.getByTestId("slot-back-room"));
    expect(await screen.findByTestId("slots-room", {}, { timeout: 8000 })).toBeTruthy();
    expect(useAuthStore.getState().accessToken).toBe("aaa.bbb.ccc");
    view.unmount();
  }, 20000);

  it("supports browser back from machine to hall to lobby", async () => {
    const view = mount("/casino/slots/buffalo-fortune", ["/casino/lobby", "/casino/slots", "/casino/slots/buffalo-fortune"]);
    expect(await screen.findByTestId("slot-game-screen")).toBeTruthy();
    fireEvent.click(screen.getByTestId("slot-back-room"));
    expect(await screen.findByTestId("slots-room", {}, { timeout: 8000 })).toBeTruthy();
    fireEvent.click(screen.getByTestId("slots-back-hall"));
    expect(await screen.findByTestId("casino-lobby", {}, { timeout: 8000 })).toBeTruthy();
    view.unmount();
  }, 20000);

  it("Phase 4.5: seated cabinet keeps identity, clips reels, and drives the shared engine", async () => {
    vi.useFakeTimers();
    const view = render(
      <MemoryRouter initialEntries={["/casino/slots/olympus-crown"]}>
        <Routes>
          <Route path="/casino/slots/:machineId" element={<SlotGameScreen />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByTestId("slot-game-screen").getAttribute("data-seated")).toBe("true");
    expect(screen.getByTestId("seated-cabinet")).toBeTruthy();
    expect(screen.getByTestId("slot-seated-asset-olympus-crown").getAttribute("src")).toContain("olympus-crown.png");
    expect(screen.queryByTestId("slot-chair-olympus-crown")).toBeNull();
    const viewport = screen.getByTestId("slot-preview-seated");
    expect(viewport.style.overflow || getComputedStyle(viewport).overflow).toBeDefined();
    expect(screen.getByTestId("slot-reels").querySelectorAll(".op-cab-reel").length).toBe(5);
    fireEvent.click(screen.getByTestId("slot-bet-plus"));
    expect(screen.getByTestId("slot-demo-bet").textContent).toBe("25");
    fireEvent.click(screen.getByTestId("slot-spin"));
    expect((screen.getByTestId("slot-spin") as HTMLButtonElement).disabled).toBe(true);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1300);
    });
    expect((screen.getByTestId("slot-spin") as HTMLButtonElement).disabled).toBe(false);
    view.unmount();
    vi.useRealTimers();
  });

  it("Phase 4.5 CSS supports reduced-motion seated play", () => {
    const css = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "seatedCabinet.css"), "utf8");
    expect(css).toMatch(/prefers-reduced-motion/);
    expect(css).toMatch(/op-seated-screen/);
    expect(css).toMatch(/overflow:\s*hidden/);
    expect(css).not.toMatch(/turquoise/);
  });

  it("Phase 4.6: seated composition works for all six machines with identity preserved", () => {
    for (const item of SLOT_CATALOG) {
      const view = render(
        <MemoryRouter initialEntries={[`/casino/slots/${item.id}`]}>
          <Routes>
            <Route path="/casino/slots/:machineId" element={<SlotGameScreen />} />
          </Routes>
        </MemoryRouter>,
      );
      const screenRoot = view.getByTestId("slot-game-screen");
      expect(screenRoot.getAttribute("data-seated")).toBe("true");
      expect(screenRoot.getAttribute("data-machine")).toBe(item.id);
      expect(screenRoot.getAttribute("data-pov")).toBe("first-person");
      expect(view.getByTestId(`slot-seated-asset-${item.id}`).getAttribute("src")).toBe(
        `/assets/casino/slots/cabinets/${item.id}.png`,
      );
      expect(view.getByTestId("seated-armchair")).toBeTruthy();
      expect(view.getByTestId("seated-ashtray")).toBeTruthy();
      expect(view.queryByTestId(`slot-chair-${item.id}`)).toBeNull();
      const close = Number.parseFloat(view.getByTestId("seated-cabinet").style.getPropertyValue("--seated-h"));
      expect(close).toBeGreaterThanOrEqual(150);
      expect(seatedCrop(item).heightPct).toBeGreaterThanOrEqual(150);
      view.unmount();
    }
  });

  it("Phase 4.6: physical BET 10/25/50/100, AUTO, HISTORY, and spin lock drive the shared engine", async () => {
    vi.useFakeTimers();
    const view = render(
      <MemoryRouter initialEntries={["/casino/slots/olympus-crown"]}>
        <Routes>
          <Route path="/casino/slots/:machineId" element={<SlotGameScreen />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(view.queryByTestId("slot-web-panel")).toBeNull();
    expect(view.getByTestId("slot-history-toggle").closest("[data-testid='seated-cabinet']")).toBeTruthy();
    expect(view.getByTestId("slot-spin").closest("[data-testid='seated-cabinet']")).toBeTruthy();
    expect(view.getByTestId("slot-auto").closest("[data-testid='seated-cabinet']")).toBeTruthy();
    expect(document.querySelector(".op-seated-hud")?.textContent).not.toMatch(/SPIN|AUTO|HISTORY|Balance/);

    const start = Number(view.getByTestId("slot-demo-balance").textContent);
    for (const n of [10, 25, 50, 100] as const) {
      fireEvent.click(view.getByTestId(`slot-bet-${n}`));
      expect(view.getByTestId("slot-demo-bet").textContent).toBe(String(n));
    }
    fireEvent.click(view.getByTestId("slot-bet-50"));
    expect(view.getByTestId("slot-demo-bet").textContent).toBe("50");
    fireEvent.click(view.getByTestId("slot-spin"));
    fireEvent.click(view.getByTestId("slot-spin"));
    expect((view.getByTestId("slot-spin") as HTMLButtonElement).disabled).toBe(true);
    expect(Number(view.getByTestId("slot-demo-balance").textContent)).toBe(start - 50);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1300);
    });
    expect((view.getByTestId("slot-spin") as HTMLButtonElement).disabled).toBe(false);
    const afterSpin = Number(view.getByTestId("slot-demo-balance").textContent);
    const win = Number(view.getByTestId("slot-demo-win").textContent);
    expect(afterSpin).toBe(start - 50 + win);

    fireEvent.click(view.getByTestId("slot-history-toggle"));
    expect(view.getByTestId("slot-history").textContent).toMatch(/Olympus Crown/);
    expect(view.getByTestId("slot-history").closest("[data-testid='seated-cabinet']")).toBeTruthy();

    fireEvent.click(view.getByTestId("slot-auto"));
    expect(view.getByTestId("slot-auto").className).toContain("is-on");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    expect((view.getByTestId("slot-spin") as HTMLButtonElement).disabled).toBe(true);
    view.unmount();
    vi.useRealTimers();
  });

  it("Phase 4.6: screen containment is preserved for every cabinet geometry", () => {
    const css = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "seatedCabinet.css"), "utf8");
    expect(css).toMatch(/clip-path:\s*inset/);
    expect(css).toMatch(/contain:\s*paint/);
    expect(css).not.toMatch(/max-width:\s*min\(46vw,\s*28rem\)/);
    expect(css).not.toMatch(/height:\s*84%/);
    expect(css).toMatch(/op-seated-vignette/);
    expect(css).toMatch(/op-seated-arm/);
    expect(css).toMatch(/100dvh - 4\.2rem/);
    for (const item of SLOT_CATALOG) {
      const glass = cabinetScreenRect(item);
      const layout = cabinetPlayLayout(item);
      expect(overlayWithinUnitSquare(layout.screen)).toBe(true);
      expect(overlayWithinUnitSquare(layout.touch)).toBe(true);
      expect(overlayWithinUnitSquare(layout.deck)).toBe(true);
      expect(overlayWithinUnitSquare(layout.spin)).toBe(true);
      expect(overlayContainedIn(glass, layout.screen)).toBe(true);
      expect(layout.touch.topPct).toBeGreaterThan(layout.screen.topPct + layout.screen.heightPct);
      const view = render(
        <MemoryRouter initialEntries={[`/casino/slots/${item.id}`]}>
          <Routes>
            <Route path="/casino/slots/:machineId" element={<SlotGameScreen />} />
          </Routes>
        </MemoryRouter>,
      );
      const glassEl = view.getByTestId("slot-preview-seated");
      expect(glassEl.style.overflow).toBe("hidden");
      expect(glassEl.contains(view.getByTestId("slot-reels"))).toBe(true);
      view.unmount();
    }
  });

  it("Phase 4.6: back returns to the Slots Hall without a detached web control card", async () => {
    const view = mount("/casino/slots/candy-fortune");
    expect(await screen.findByTestId("slot-game-screen", {}, { timeout: 8000 })).toBeTruthy();
    expect(screen.getByTestId("slot-controls-seated")).toBeTruthy();
    expect(screen.queryByTestId("slot-web-panel")).toBeNull();
    fireEvent.click(screen.getByTestId("slot-back-room"));
    expect(await screen.findByTestId("slots-room", {}, { timeout: 8000 })).toBeTruthy();
    expect(screen.getByTestId("slots-catalog").querySelectorAll(".op-phys-cab")).toHaveLength(6);
    view.unmount();
  }, 20000);

  it("does not regress roulette, blackjack or poker rooms", () => {
    expect(render(<MemoryRouter><RouletteHall /></MemoryRouter>).getByTestId("roulette-hall")).toBeTruthy();
    expect(render(<MemoryRouter><BlackjackSalon /></MemoryRouter>).getByTestId("blackjack-room")).toBeTruthy();
    expect(render(<MemoryRouter><PokerRoom /></MemoryRouter>).getByTestId("poker-room")).toBeTruthy();
  });

  it("keeps the existing Odessa Gold route inside the casino shell", async () => {
    mount("/casino/slots/odessa-gold");
    expect(await screen.findByTestId("odessa-gold", {}, { timeout: 8000 })).toBeTruthy();
    expect(screen.getByTestId("casino-shell")).toBeTruthy();
  }, 20000);
});
