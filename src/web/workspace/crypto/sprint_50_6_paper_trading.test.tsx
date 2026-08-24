/**
 * Sprint 50.6 — paper trading UI: submit, refresh, errors, open/close, journal, no raw DB-only inputs.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { JournalPanel, PaperTradingPanel } from "./paperTradingPanels";

function wrap(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("sprint 50.6 paper trading UI", () => {
  it("submit form calls create endpoint payload via onPlace", async () => {
    const onPlace = vi.fn().mockResolvedValue(undefined);
    wrap(
      <PaperTradingPanel
        account={{ balance: 100000 }}
        orders={[]}
        positions={[]}
        onPlace={onPlace}
        onClose={() => undefined}
        onRefresh={() => undefined}
        quoteMid={1.085}
      />,
    );
    fireEvent.click(screen.getByTestId("paper-open-btn"));
    await waitFor(() => expect(onPlace).toHaveBeenCalledTimes(1));
    const body = onPlace.mock.calls[0][0] as Record<string, unknown>;
    expect(body.action).toBe("place");
    expect(body.instrument).toBe("EUR/USD");
    expect(body.idempotency_key).toBeTruthy();
  });

  it("successful response path refreshes lists via onPlace then parent load", async () => {
    const onRefresh = vi.fn().mockResolvedValue(undefined);
    const onPlace = vi.fn().mockImplementation(async () => {
      await onRefresh();
    });
    wrap(
      <PaperTradingPanel
        account={{ balance: 100000 }}
        orders={[]}
        positions={[]}
        onPlace={onPlace}
        onClose={() => undefined}
        onRefresh={onRefresh}
        quoteMid={1.085}
      />,
    );
    fireEvent.click(screen.getByTestId("paper-open-btn"));
    await waitFor(() => expect(onRefresh).toHaveBeenCalled());
  });

  it("failed response displays error message", () => {
    wrap(
      <PaperTradingPanel
        account={{ balance: 100000 }}
        orders={[]}
        positions={[]}
        onPlace={() => undefined}
        onClose={() => undefined}
        onRefresh={() => undefined}
        message="Stop Loss для BUY должен быть ниже цены входа"
        quoteMid={1.085}
      />,
    );
    expect(screen.getByTestId("paper-form-message").textContent).toContain("Stop Loss");
  });

  it("open position renders and close button calls endpoint", () => {
    const onClose = vi.fn();
    wrap(
      <PaperTradingPanel
        account={{ balance: 100000 }}
        orders={[{ order_id: "po_1", instrument: "EUR/USD", order_type: "MARKET", status: "FILLED", created_at: "2026-08-12" }]}
        positions={[
          {
            position_id: "pp_1",
            instrument: "EUR/USD",
            side: "BUY",
            entry_price: 1.085,
            status: "OPEN",
            stop_loss: 1.08,
            take_profit: 1.09,
          },
        ]}
        onPlace={() => undefined}
        onClose={onClose}
        onRefresh={() => undefined}
      />,
    );
    expect(screen.getByText(/EUR\/USD · BUY · вход 1\.085/)).toBeTruthy();
    expect(screen.getByText(/FILLED/)).toBeTruthy();
    fireEvent.click(screen.getByTestId("paper-close-pp_1"));
    expect(onClose).toHaveBeenCalledWith("pp_1");
  });

  it("journal event renders including opened lifecycle", () => {
    wrap(
      <JournalPanel
        items={[
          {
            journal_id: "jn_1",
            event: "PAPER_POSITION_OPENED",
            instrument: "EUR/USD",
            side: "BUY",
            entry: 1.085,
            result: "open",
            created_at: "2026-08-12T10:00:00Z",
            date: "2026-08-12",
          },
        ]}
      />,
    );
    expect(screen.getByTestId("journal-table")).toBeTruthy();
    expect(screen.getByTestId("journal-table").textContent).toContain("EUR/USD");
    expect(screen.getByTestId("journal-table").textContent).toContain("open");
  });

  it("refresh button invokes onRefresh (real refetch hook)", async () => {
    const onRefresh = vi.fn().mockResolvedValue(undefined);
    wrap(
      <PaperTradingPanel
        account={{ balance: 100000 }}
        orders={[]}
        positions={[]}
        onPlace={() => undefined}
        onClose={() => undefined}
        onRefresh={onRefresh}
      />,
    );
    fireEvent.click(screen.getByTestId("paper-refresh-btn"));
    await waitFor(() => expect(onRefresh).toHaveBeenCalledTimes(1));
  });

  it("raw database ID inputs are removed — only optional linkage placeholders", () => {
    wrap(
      <PaperTradingPanel
        account={{ balance: 100000 }}
        orders={[]}
        positions={[]}
        onPlace={() => undefined}
        onClose={() => undefined}
        onRefresh={() => undefined}
      />,
    );
    expect(screen.queryByPlaceholderText(/database id/i)).toBeNull();
    expect(screen.queryByLabelText(/raw db/i)).toBeNull();
    expect(screen.getByTestId("paper-link-signal")).toBeTruthy();
    expect(screen.getByTestId("paper-link-analysis")).toBeTruthy();
  });

  it("open button shows Открываем… while pending and disables double submit", async () => {
    let resolve!: () => void;
    const gate = new Promise<void>((r) => {
      resolve = r;
    });
    const onPlace = vi.fn().mockImplementation(() => gate);
    wrap(
      <PaperTradingPanel
        account={{ balance: 100000 }}
        orders={[]}
        positions={[]}
        onPlace={onPlace}
        onClose={() => undefined}
        onRefresh={() => undefined}
      />,
    );
    const btn = screen.getByTestId("paper-open-btn");
    fireEvent.click(btn);
    await waitFor(() => expect(btn.textContent).toContain("Открываем"));
    expect((btn as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(btn);
    expect(onPlace).toHaveBeenCalledTimes(1);
    resolve();
    await waitFor(() => expect(btn.textContent).toContain("Открыть бумажную сделку"));
  });
});
