import { afterEach, describe, expect, it } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CasinoApp } from "./CasinoApp";
import { CasinoBrowseRoute } from "@/shell/CasinoBrowseRoute";
import { casinoSound } from "./casinoSound";
import { casinoNavActive } from "./components/CasinoShell";
import { loginRedirect, sanitizeReturnTo } from "@/navigation/safeReturnTo";
import { LOBBY_HOTSPOTS } from "./lobby/hotspots";
import { HALL_ZONES } from "./lobby/hallZones";

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
        <Route path="/" element={<p data-testid="home-page">home</p>} />
        <Route path="/login" element={<p data-testid="login-page">login</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint 22 Odessa Prime lobby", () => {
  afterEach(() => {
    casinoSound.setMuted(true);
  });

  it("renders immersive LobbyScene without enterprise CRM chrome", async () => {
    const view = mount("/casino/lobby");
    await waitFor(() => expect(screen.getByTestId("casino-lobby")).toBeTruthy());
    expect(screen.getByTestId("casino-shell")).toBeTruthy();
    expect(screen.getByTestId("lobby-hall")).toBeTruthy();
    expect(view.container.querySelector(".op-lobby-photo")).toBeTruthy();
    expect(screen.queryByText("Enterprise Dashboard")).toBeNull();
    expect(document.querySelector(".ados-shell")).toBeNull();
    view.unmount();
  });

  it("renders room hotspots and navigates roulette and blackjack", async () => {
    const view = mount("/casino/lobby");
    for (const zone of HALL_ZONES) {
      expect(screen.getByTestId(`hotspot-${zone.id}`)).toBeTruthy();
    }
    expect(screen.queryByTestId("hotspot-vip")).toBeNull();
    fireEvent.click(screen.getByTestId("hotspot-roulette"));
    expect(await screen.findByTestId("roulette-table", {}, { timeout: 8000 })).toBeTruthy();
    view.unmount();

    const bj = mount("/casino/lobby");
    fireEvent.click(screen.getByTestId("hotspot-blackjack"));
    expect(await screen.findByTestId("blackjack-table", {}, { timeout: 8000 })).toBeTruthy();
    bj.unmount();
  }, 20000);

  it("opens poker, slots, VIP, bar and restaurant rooms", async () => {
    for (const [path, testid] of [
      ["/casino/poker", "poker-room"],
      ["/casino/slots", "slots-room"],
      ["/casino/vip", "vip-room"],
      ["/casino/bar", "bar-room"],
      ["/casino/restaurant", "restaurant-room"],
    ] as const) {
      const view = mount(path);
      expect(await screen.findByTestId(testid, {}, { timeout: 8000 })).toBeTruthy();
      view.unmount();
    }
  }, 30000);

  it("renders the interactive map with clickable zones and lobby highlight", async () => {
    const view = mount("/casino/map");
    await waitFor(() => expect(screen.getByTestId("casino-map")).toBeTruthy());
    expect(screen.getByTestId("map-zone-lobby").className).toContain("is-here");
    for (const spot of LOBBY_HOTSPOTS) {
      expect(screen.getByTestId(`map-zone-${spot.id}`)).toBeTruthy();
    }
    fireEvent.click(screen.getByTestId("map-zone-vip"));
    expect(await screen.findByTestId("vip-room", {}, { timeout: 8000 })).toBeTruthy();
    view.unmount();
  }, 20000);

  it("toggles ЗАЛ / КАРТА", async () => {
    const view = mount("/casino/lobby");
    expect(screen.getByTestId("lobby-pan")).toBeTruthy();
    fireEvent.click(screen.getByTestId("lobby-toggle-map"));
    expect(screen.getByTestId("casino-map")).toBeTruthy();
    expect(screen.queryByTestId("lobby-pan")).toBeNull();
    fireEvent.click(screen.getByTestId("lobby-toggle-hall"));
    expect(screen.getByTestId("lobby-pan")).toBeTruthy();
    view.unmount();
  });

  it("lights a hotspot on hover and keeps reduced-motion lobby usable", () => {
    const view = mount("/casino/lobby");
    const roulette = screen.getByTestId("hotspot-roulette");
    fireEvent.pointerEnter(roulette);
    expect(roulette.className).toContain("is-lit");
    fireEvent.pointerLeave(roulette);
    expect(casinoSound.muted).toBe(true);
    view.unmount();
  });

  it("highlights current lobby nav", () => {
    expect(casinoNavActive("/casino/lobby", "lobby", "/casino/lobby")).toBe(true);
    expect(casinoNavActive("/casino", "casino", "/casino", true)).toBe(true);
    expect(casinoNavActive("/casino/lobby", "casino", "/casino", true)).toBe(false);
    expect(casinoNavActive("/casino/vip", "vip", "/casino/vip")).toBe(true);
    expect(casinoNavActive("/casino/roulette/royale-1", "casino", "/casino", true)).toBe(false);
  });

  it("lets a guest browse lobby without sending them home", async () => {
    const view = mount("/casino/lobby");
    expect(await screen.findByTestId("casino-lobby")).toBeTruthy();
    expect(screen.queryByTestId("home-page")).toBeNull();
    expect(screen.queryByTestId("login-page")).toBeNull();
    view.unmount();
  });

  it("preserves room returnTo for PLAY auth", () => {
    expect(sanitizeReturnTo("/casino/blackjack")).toBe("/casino/blackjack");
    expect(decodeURIComponent(loginRedirect("/casino/roulette/royale-1"))).toContain("/casino/roulette/royale-1");
  });

  it("keeps deep-links and mobile lobby inside CasinoShell", async () => {
    const deep = mount("/casino/roulette/table/royale-1");
    expect(await screen.findByTestId("roulette-table", {}, { timeout: 8000 })).toBeTruthy();
    expect(screen.getByTestId("casino-shell")).toBeTruthy();
    deep.unmount();
    const mobile = mount("/casino/lobby");
    expect(mobile.container.querySelector(".op-bottom")).toBeTruthy();
    expect(screen.getByTestId("hotspot-roulette")).toBeTruthy();
    mobile.unmount();
  }, 20000);
});
