import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CasinoApp } from "./CasinoApp";
import { resolvePerformanceTier } from "./hooks/usePerformanceTier";
import { roomToneFromPath } from "./audio/casinoAudio";
import { sanitizeReturnTo } from "@/navigation/safeReturnTo";
import { CASINO_ROUTES } from "./state/casinoRoutes";
import { PokerRoom } from "./rooms/PokerRoom";
import { VipRoom } from "./rooms/VipRoom";
import { BarRoom } from "./rooms/BarRoom";
import { RestaurantRoom } from "./rooms/RestaurantRoom";
import { LobbyScene } from "./scenes/LobbyScene";

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
    expect(CASINO_ROUTES.lobbyAlias).toBe("/casino/lobby");
    expect(sanitizeReturnTo("/casino/rooms/vip")).toBe("/casino/rooms/vip");
    expect(sanitizeReturnTo("/casino/poker")).toBe("/casino/poker");
    expect(roomToneFromPath("/casino/rooms/bar")).toBe("bar");
    expect(roomToneFromPath("/casino")).toBe("entrance");
  });

  it("renders lobby hotspots for every live room", () => {
    render(
      <MemoryRouter>
        <LobbyScene />
      </MemoryRouter>,
    );
    for (const id of ["roulette", "blackjack", "slots", "poker", "vip", "bar", "restaurant"]) {
      expect(screen.getByTestId(`hotspot-${id}`)).toBeTruthy();
    }
    expect(screen.getByTestId("lobby-pan")).toBeTruthy();
  });

  it("renders atmosphere rooms without claiming gameplay", () => {
    const poker = render(
      <MemoryRouter>
        <PokerRoom />
      </MemoryRouter>,
    );
    expect(poker.getByTestId("poker-room")).toBeTruthy();
    expect(poker.getByText(/Раздача и банк/i)).toBeTruthy();
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
    await waitFor(() => expect(screen.getByTestId("casino-lobby")).toBeTruthy());
    expect(lobby.container.querySelector('[data-testid="casino-shell"]')).toBeTruthy();
    lobby.unmount();

    const poker = mount("/casino/rooms/poker");
    await waitFor(() => expect(screen.getByTestId("poker-room")).toBeTruthy());
    poker.unmount();

    const alias = mount("/casino/vip");
    await waitFor(() => expect(screen.getByTestId("vip-room")).toBeTruthy());
    alias.unmount();
  });
});
