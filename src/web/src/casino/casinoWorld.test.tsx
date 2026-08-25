import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import type { ReactElement } from "react";
import { CASINO_ROUTES } from "./state/casinoRoutes";
import { LobbyScene } from "./scenes/LobbyScene";
import { EntranceScene } from "./scenes/EntranceScene";
import { wheelDegreesForNumber, EUROPEAN_ORDER } from "./games/roulette/wheelMath";
import { useBetLock } from "./hooks/useBetLock";
import { chipFlightDuration } from "./games/roulette/chipMotion";
import { loginRedirect, sanitizeReturnTo } from "@/navigation/safeReturnTo";
import { RouletteHall } from "./rooms/RouletteHall";
import { BlackjackSalon } from "./rooms/BlackjackSalon";
import { SlotParlor } from "./rooms/SlotParlor";
import { OdessaGoldMachine } from "./games/slots/OdessaGoldMachine";
import { CasinoApp } from "./CasinoApp";

function wrap(ui: ReactElement, path = "/casino/floor") {
  return <MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter>;
}

describe("Sprint 18 immersive world", () => {
  it("exposes room and game routes", () => {
    expect(CASINO_ROUTES.lobby).toBe("/casino");
    expect(CASINO_ROUTES.floor).toBe("/casino/floor");
    expect(CASINO_ROUTES.rouletteHall).toBe("/casino/rooms/roulette");
    expect(CASINO_ROUTES.blackjackRoom).toBe("/casino/rooms/blackjack");
    expect(CASINO_ROUTES.slotsRoom).toBe("/casino/rooms/slots");
    expect(CASINO_ROUTES.table("roulette-royale-1")).toBe("/casino/roulette/roulette-royale-1");
    expect(CASINO_ROUTES.slot("odessa-gold")).toBe("/casino/slots/odessa-gold");
  });

  it("maps wheel degrees from server number", () => {
    expect(EUROPEAN_ORDER).toHaveLength(37);
    expect(wheelDegreesForNumber(0, 0)).not.toBe(wheelDegreesForNumber(32, 0));
    expect(wheelDegreesForNumber(17, 6)).toBeGreaterThan(2000);
  });

  it("locks bets outside BETTING_OPEN", () => {
    function Probe({ phase }: { phase: string }) {
      const lock = useBetLock(phase);
      return <span>{lock.locked ? "locked" : "open"}</span>;
    }
    const locked = render(<Probe phase="SPINNING" />);
    expect(locked.getByText("locked")).toBeTruthy();
    locked.unmount();
    const open = render(<Probe phase="BETTING_OPEN" />);
    expect(open.getByText("open")).toBeTruthy();
    expect(chipFlightDuration(100)).toBeGreaterThan(200);
  });

  it("keeps casino returnTo allowlisted", () => {
    expect(sanitizeReturnTo("/casino/rooms/blackjack")).toBe("/casino/rooms/blackjack");
    expect(sanitizeReturnTo("/casino/slots/odessa-gold")).toBe("/casino/slots/odessa-gold");
    expect(loginRedirect("/casino/rooms/roulette")).toContain("returnTo=");
  });

  it("renders entrance, lobby hotspots and roulette hall", () => {
    const entrance = render(wrap(<EntranceScene />, "/casino"));
    expect(entrance.getByTestId("casino-entrance")).toBeTruthy();
    entrance.unmount();
    const lobby = render(wrap(<LobbyScene />));
    expect(lobby.getByTestId("hotspot-roulette")).toBeTruthy();
    expect(lobby.getByTestId("hotspot-blackjack")).toBeTruthy();
    expect(lobby.getByTestId("hotspot-vip")).toBeTruthy();
    expect(lobby.getByTestId("hotspot-poker")).toBeTruthy();
    expect(lobby.getByText("ЗАЛ")).toBeTruthy();
    expect(lobby.getByText("КАРТА")).toBeTruthy();
    lobby.unmount();
    const hall = render(wrap(<RouletteHall />, "/casino/rooms/roulette"));
    expect(hall.getByTestId("roulette-hall")).toBeTruthy();
    expect(hall.getByTestId("roulette-dealer")).toBeTruthy();
  });

  it("renders blackjack and slot machines with animation hooks", () => {
    const bj = render(wrap(<BlackjackSalon />, "/casino/rooms/blackjack"));
    expect(bj.getByTestId("blackjack-room")).toBeTruthy();
    expect(bj.getByTestId("bj-hit")).toBeTruthy();
    bj.unmount();
    const slots = render(wrap(<SlotParlor />, "/casino/rooms/slots"));
    expect(slots.getByTestId("slots-room")).toBeTruthy();
    slots.unmount();
    const gold = render(wrap(<OdessaGoldMachine />, "/casino/slots/odessa-gold"));
    expect(gold.getByTestId("odessa-gold")).toBeTruthy();
    expect(gold.getByTestId("slot-reels")).toBeTruthy();
  });

  it("mounts casino app shell without workspace chrome", () => {
    render(
      <MemoryRouter initialEntries={["/casino"]}>
        <Routes>
          <Route path="/casino/*" element={<CasinoApp />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByTestId("casino-shell")).toBeTruthy();
    expect(screen.queryByText("Enterprise Dashboard")).toBeNull();
  });
});
