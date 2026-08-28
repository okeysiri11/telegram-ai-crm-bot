import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CasinoApp } from "./CasinoApp";
import { resolvePerformanceTier } from "./hooks/usePerformanceTier";
import { roomToneFromPath } from "./audio/casinoAudio";
import { sanitizeReturnTo } from "@/navigation/safeReturnTo";
import { CASINO_ROUTES, resolveRouletteTableId } from "./state/casinoRoutes";
import { PokerRoom } from "./rooms/PokerRoom";
import { VipRoom } from "./rooms/VipRoom";
import { BarRoom } from "./rooms/BarRoom";
import { RestaurantRoom } from "./rooms/RestaurantRoom";
import { LobbyScene } from "./scenes/LobbyScene";
import { CasinoGuestModal } from "./components/CasinoGuestModal";

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/casino/*" element={<CasinoApp />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint 19 live casino", () => {
  it("resolves HIGH / MEDIUM / LOW performance tiers", () => {
    expect(resolvePerformanceTier({ width: 1920, dpr: 1, cores: 8, reducedMotion: false })).toBe("HIGH");
    expect(resolvePerformanceTier({ width: 1366, dpr: 1, cores: 4, reducedMotion: false })).toBe("MEDIUM");
    expect(
      resolvePerformanceTier({ width: 360, dpr: 3, cores: 4, reducedMotion: false, touch: true }),
    ).toBe("LOW");
    expect(resolvePerformanceTier({ width: 1920, dpr: 1, cores: 8, reducedMotion: true })).toBe("LOW");
  });

  it("exposes atmosphere room routes and lobby alias", () => {
    expect(CASINO_ROUTES.pokerRoom).toBe("/casino/rooms/poker");
    expect(CASINO_ROUTES.vipRoom).toBe("/casino/rooms/vip");
    expect(CASINO_ROUTES.barRoom).toBe("/casino/rooms/bar");
    expect(CASINO_ROUTES.restaurantRoom).toBe("/casino/rooms/restaurant");
    expect(CASINO_ROUTES.rouletteLive).toBe("/casino/roulette/royale-1");
    expect(sanitizeReturnTo("/casino/roulette/table/royale-1")).toBe("/casino/roulette/table/royale-1");
    expect(sanitizeReturnTo("/casino/rooms/vip")).toBe("/casino/rooms/vip");
    expect(sanitizeReturnTo("/casino/poker")).toBe("/casino/poker");
    expect(roomToneFromPath("/casino/rooms/bar")).toBe("bar");
    expect(resolveRouletteTableId("royale-1")).toBe("roulette-royale-1");
    expect(resolveRouletteTableId("table")).toBe("roulette-royale-1");
  });

  it("renders lobby hotspots for every live room", () => {
    render(
      <MemoryRouter>
        <LobbyScene />
      </MemoryRouter>,
    );
    for (const id of ["roulette", "blackjack", "poker", "restaurant", "bar", "slots"]) {
      expect(screen.getByTestId(`hotspot-${id}`)).toBeTruthy();
    }
    expect(screen.queryByTestId("hotspot-vip")).toBeNull();
    expect(screen.getByTestId("lobby-pan")).toBeTruthy();
  });

  it("renders atmosphere rooms without claiming gameplay", () => {
    const poker = render(
      <MemoryRouter>
        <PokerRoom />
      </MemoryRouter>,
    );
    expect(poker.getByTestId("poker-room")).toBeTruthy();
    expect(poker.getByText("POKER ROOM")).toBeTruthy();
    poker.unmount();
    expect(
      render(
        <MemoryRouter>
          <VipRoom />
        </MemoryRouter>,
      ).getByTestId("vip-room"),
    ).toBeTruthy();
    expect(
      render(
        <MemoryRouter>
          <BarRoom />
        </MemoryRouter>,
      ).getByTestId("bar-room"),
    ).toBeTruthy();
    expect(
      render(
        <MemoryRouter>
          <RestaurantRoom />
        </MemoryRouter>,
      ).getByTestId("restaurant-room"),
    ).toBeTruthy();
  });

  it("resolves direct room routes and lobby alias through CasinoApp", async () => {
    const lobby = mount("/casino/lobby");
    expect(await screen.findByTestId("casino-lobby", {}, { timeout: 8000 })).toBeTruthy();
    expect(lobby.container.querySelector('[data-testid="casino-shell"]')).toBeTruthy();
    lobby.unmount();

    const poker = mount("/casino/rooms/poker");
    expect(await screen.findByTestId("poker-room", {}, { timeout: 8000 })).toBeTruthy();
    poker.unmount();

    const table = mount("/casino/roulette/table/royale-1");
    expect(await screen.findByTestId("roulette-table", {}, { timeout: 8000 })).toBeTruthy();
    table.unmount();

    const alias = mount("/casino/vip");
    expect(await screen.findByTestId("vip-room", {}, { timeout: 8000 })).toBeTruthy();
    alias.unmount();

    const bj = mount("/casino/blackjack");
    expect(await screen.findByTestId("blackjack-room", {}, { timeout: 8000 })).toBeTruthy();
    expect(screen.getByText("СДАТЬ")).toBeTruthy();
    expect(screen.getByText("ЕЩЁ")).toBeTruthy();
    expect(screen.getByText("ХВАТИТ")).toBeTruthy();
    expect(screen.getByText("УДВОИТЬ")).toBeTruthy();
    bj.unmount();

    const unknown = mount("/casino/missing-hall");
    expect(await screen.findByTestId("casino-unknown", {}, { timeout: 8000 })).toBeTruthy();
    expect(screen.queryByTestId("casino-entrance")).toBeNull();
    unknown.unmount();
  }, 30000);

  it("opens guest modal without leaving the casino", () => {
    render(
      <MemoryRouter>
        <CasinoGuestModal returnTo="/casino/roulette/table/royale-1" onClose={() => undefined} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("casino-guest-modal")).toBeTruthy();
    const login = screen.getByText("ВОЙТИ") as HTMLAnchorElement;
    expect(login.getAttribute("href") || "").toContain("returnTo=");
    expect(decodeURIComponent(login.getAttribute("href") || "")).toContain("/casino/roulette/table/royale-1");
    expect(screen.getByText("ОСТАТЬСЯ ГОСТЕМ")).toBeTruthy();
  });
});
