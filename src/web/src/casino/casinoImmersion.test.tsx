import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CasinoApp } from "./CasinoApp";
import { EntranceScene } from "./scenes/EntranceScene";

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/casino/*" element={<CasinoApp />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint 21 visual immersion", () => {
  it("applies Odessa Prime art direction on the casino shell", async () => {
    const view = mount("/casino");
    await waitFor(() => expect(screen.getByTestId("casino-shell")).toBeTruthy());
    expect(screen.getByTestId("casino-shell").getAttribute("data-art")).toBe("odessa-prime");
    expect(screen.getByTestId("casino-entrance")).toBeTruthy();
    view.unmount();
  });

  it("renders entrance materials: marble, brass, fog, lamp pool", () => {
    const view = render(
      <MemoryRouter>
        <EntranceScene />
      </MemoryRouter>,
    );
    expect(view.container.querySelector(".op-marble")).toBeTruthy();
    expect(view.container.querySelector(".op-brass-arch")).toBeTruthy();
    expect(view.container.querySelector(".op-fog")).toBeTruthy();
    expect(view.container.querySelector(".op-lamp-pool")).toBeTruthy();
    expect(view.container.querySelector(".op-runner")).toBeTruthy();
    view.unmount();
  });

  it("shows a shared threshold veil when leaving the lobby for a live table", async () => {
    const view = mount("/casino/lobby");
    await waitFor(() => expect(screen.getByTestId("casino-lobby")).toBeTruthy());
    expect(screen.queryByTestId("room-transition")).toBeNull();
    fireEvent.click(screen.getByTestId("hotspot-roulette"));
    expect(screen.getByTestId("room-transition")).toBeTruthy();
    expect(view.container.querySelector(".op-transition-brass")).toBeTruthy();
    view.unmount();
  });

  it("presents roulette as a lit pit with wood rail and lamp", async () => {
    const view = mount("/casino/roulette/table/royale-1");
    await waitFor(() => expect(screen.getByTestId("roulette-table")).toBeTruthy());
    expect(view.container.querySelector(".op-pit")).toBeTruthy();
    expect(view.container.querySelector(".op-table-lamp")).toBeTruthy();
    expect(view.container.querySelector(".op-wood-rail")).toBeTruthy();
    expect(screen.getByTestId("roulette-table").getAttribute("data-phase")).toBe("BETTING_OPEN");
    view.unmount();
  });

  it("keeps blackjack salon playable under table lighting", async () => {
    const view = mount("/casino/blackjack");
    await waitFor(() => expect(screen.getByTestId("blackjack-table")).toBeTruthy());
    expect(view.container.querySelector(".op-bj-lamp")).toBeTruthy();
    expect(view.container.querySelector(".op-bj-rail")).toBeTruthy();
    expect(screen.getByText("СДАТЬ")).toBeTruthy();
    expect(screen.getByText("ЕЩЁ")).toBeTruthy();
    expect(screen.getByText("ХВАТИТ")).toBeTruthy();
    expect(screen.getByText("УДВОИТЬ")).toBeTruthy();
    view.unmount();
  });
});
