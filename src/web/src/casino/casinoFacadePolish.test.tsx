/**
 * Odessa Prime Casino — facade visual polish + premium cards + lazy rooms.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CasinoApp } from "./CasinoApp";
import { CARD_VISUALS } from "./entrance/cardVisuals";
import { ENTRANCE_PREVIEWS } from "./entrance/CasinoGamePreviewStrip";

afterEach(() => {
  cleanup();
});

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/casino/*" element={<CasinoApp />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Odessa Prime facade polish", () => {
  it("renders the /casino facade, hero, CTA and six premium cards", () => {
    const view = mount("/casino");
    expect(screen.getByTestId("casino-shell")).toBeTruthy();
    expect(screen.getByTestId("casino-entrance")).toBeTruthy();
    expect(screen.getByTestId("casino-hero")).toBeTruthy();
    expect(screen.getByTestId("casino-enter-cta")).toHaveTextContent("ВОЙТИ В КАЗИНО");
    expect(screen.getByTestId("casino-preview-strip")).toBeTruthy();
    for (const card of ENTRANCE_PREVIEWS) {
      const node = screen.getByTestId(`preview-${card.id}`);
      expect(node).toHaveTextContent(card.title);
      expect(node).toHaveTextContent(card.status);
      expect(node.querySelector(".op-preview-svg")).toBeTruthy();
      expect(node.querySelector(".op-preview-photo")).toHaveAttribute("src", CARD_VISUALS[card.id].src);
      expect(node.querySelector(".op-preview-photo")).toHaveAttribute("loading", "lazy");
    }
    view.unmount();
  });

  it("keeps a single casino header nav without a competing rooms bar", () => {
    const view = mount("/casino");
    expect(screen.getAllByTestId("casino-primary-nav")).toHaveLength(1);
    expect(view.container.querySelector(".op-nav-rooms")).toBeNull();
    const nav = screen.getByTestId("casino-primary-nav");
    expect(nav.textContent).toContain("ГОРОД");
    expect(nav.textContent).toContain("КАЗИНО");
    expect(nav.textContent).toContain("АКЦИИ");
    expect(nav.textContent).toContain("VIP");
    expect(nav.textContent).toContain("ТУРНИРЫ");
    expect(nav.textContent).toContain("ПОДДЕРЖКА");
    expect(nav.textContent).not.toContain("ИГРОВЫЕ ЗАЛЫ");
    view.unmount();
  });

  it("removes facade debug overlays and empty architecture boxes", () => {
    const view = mount("/casino");
    expect(view.container.querySelector(".op-doors")).toBeNull();
    expect(view.container.querySelector(".op-brass-arch")).toBeNull();
    expect(view.container.querySelector(".op-columns")).toBeNull();
    expect(view.container.textContent).not.toContain("HOTSPOT");
    view.unmount();
  });

  it("opens the existing hall from ВОЙТИ В КАЗИНО", async () => {
    const view = mount("/casino");
    fireEvent.click(screen.getByTestId("casino-enter-cta"));
    expect(await screen.findByTestId("casino-lobby", {}, { timeout: 8000 })).toBeTruthy();
    view.unmount();
  }, 20000);

  it("routes live cards and marks unavailable cards as Скоро", async () => {
    const live = mount("/casino");
    fireEvent.click(screen.getByTestId("preview-blackjack"));
    expect(await screen.findByTestId("blackjack-room", {}, { timeout: 8000 })).toBeTruthy();
    live.unmount();

    const soon = mount("/casino");
    fireEvent.click(screen.getByTestId("preview-tournaments"));
    expect(screen.getByTestId("casino-soon-modal")).toBeTruthy();
    soon.unmount();
  }, 20000);

  it("lazy-loads heavy rooms without breaking direct routes", async () => {
    const appSrc = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "CasinoApp.tsx"), "utf8");
    expect(appSrc).toMatch(/lazyCasinoPage\(\(\) => import\("\.\/rooms\/RouletteHall"\)\)/);
    expect(appSrc).toMatch(/lazyCasinoPage\(\(\) => import\("\.\/rooms\/BlackjackSalon"\)\)/);
    expect(appSrc).toMatch(/lazyCasinoPage\(\(\) => import\("\.\/rooms\/SlotParlor"\)\)/);
    expect(appSrc).toMatch(/lazyCasinoPage\(\(\) => import\("\.\/rooms\/PokerRoom"\)\)/);
    const view = mount("/casino/roulette/royale-1");
    expect(await screen.findByTestId("roulette-table", {}, { timeout: 8000 })).toBeTruthy();
    view.unmount();
  }, 20000);

  it("uses CSS hover rather than React hover state on cards", () => {
    const src = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "entrance/CasinoGamePreviewStrip.tsx"), "utf8");
    expect(src).not.toMatch(/useState/);
    expect(src).not.toMatch(/onMouseMove/);
    const css = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "assets/entrance.css"), "utf8");
    expect(css).toMatch(/\.op-preview-card:hover/);
    expect(css).toMatch(/transform:\s*scale\(1\.04\)/);
    expect(css).not.toMatch(/backdrop-filter/);
  });
});
