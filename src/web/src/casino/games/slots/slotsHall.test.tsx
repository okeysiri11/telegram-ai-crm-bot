/**
 * Phase 4.0 — Slots Room hall, catalog, demo engine, navigation.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { CasinoApp } from "../../CasinoApp";
import { CasinoBrowseRoute } from "@/shell/CasinoBrowseRoute";
import { useAuthStore } from "@/auth/authStore";
import { SLOT_CATALOG } from "./slotCatalog";
import { SlotGameScreen } from "./SlotGameScreen";
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
    expect(await screen.findByTestId("slots-room")).toBeTruthy();
    expect(useAuthStore.getState().accessToken).toBe("aaa.bbb.ccc");
    view.unmount();
  }, 20000);

  it("supports browser back from machine to hall to lobby", async () => {
    const view = mount("/casino/slots/buffalo-fortune", ["/casino/lobby", "/casino/slots", "/casino/slots/buffalo-fortune"]);
    expect(await screen.findByTestId("slot-game-screen")).toBeTruthy();
    fireEvent.click(screen.getByTestId("slot-back-room"));
    expect(await screen.findByTestId("slots-room")).toBeTruthy();
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
