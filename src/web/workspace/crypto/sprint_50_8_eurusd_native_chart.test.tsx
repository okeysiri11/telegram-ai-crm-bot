/**
 * Sprint 50.8 — EURUSD native Lightweight Charts (no FX:EURUSD TradingView widget).
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { DualChartsPanel, eurusdSourceLabel } from "./paperTradingPanels";
import { barsToCandles, normalizeCandlesTimeframe } from "./fxNativeChartCore";
import { CHART_TIMEFRAMES } from "./chartProvider";
import { cryptoFxIntelGet } from "../business-ops/opsApi";

vi.mock("../business-ops/opsApi", () => ({
  cryptoFxIntelGet: vi.fn(),
}));

vi.mock("lightweight-charts", () => {
  const series = { setData: vi.fn(), update: vi.fn(), priceScale: () => ({ applyOptions: vi.fn() }) };
  const timeScale = {
    fitContent: vi.fn(),
    setVisibleLogicalRange: vi.fn(),
    subscribeVisibleLogicalRangeChange: vi.fn(),
    unsubscribeVisibleLogicalRangeChange: vi.fn(),
    getVisibleLogicalRange: vi.fn(() => null),
  };
  const chart = {
    addCandlestickSeries: vi.fn(() => series),
    applyOptions: vi.fn(),
    timeScale: () => timeScale,
    remove: vi.fn(),
  };
  return {
    createChart: vi.fn(() => chart),
  };
});

const okCandles = {
  ok: true,
  json: {
    status: "connected",
    chart_ready: true,
    bar_count: 2,
    source: "Yahoo Finance (EURUSD=X)",
    provider: "yahoo",
    last_close: 1.1602,
    bars: [
      { t: "2026-09-02T10:00:00+00:00", o: 1.16, h: 1.162, l: 1.158, c: 1.161 },
      { t: "2026-09-02T11:00:00+00:00", o: 1.161, h: 1.163, l: 1.159, c: 1.1602 },
    ],
  },
};

describe("sprint 50.8 EURUSD native chart", () => {
  beforeEach(() => {
    // @ts-expect-error test stub
    global.ResizeObserver = class {
      observe() {}
      disconnect() {}
      unobserve() {}
    };
    vi.mocked(cryptoFxIntelGet).mockResolvedValue(okCandles);
  });

  it("maps all required EURUSD timeframes", () => {
    expect(normalizeCandlesTimeframe("1m")).toBe("1m");
    expect(normalizeCandlesTimeframe("5m")).toBe("5m");
    expect(normalizeCandlesTimeframe("15m")).toBe("15m");
    expect(normalizeCandlesTimeframe("1h")).toBe("1H");
    expect(normalizeCandlesTimeframe("4h")).toBe("4H");
    expect(normalizeCandlesTimeframe("1D")).toBe("1D");
    expect(normalizeCandlesTimeframe("1W")).toBe("1W");
  });

  it("keeps only finite OHLC candles", () => {
    const candles = barsToCandles([
      { t: "2026-09-02T10:00:00Z", o: 1.1, h: 1.2, l: 1.0, c: 1.15 },
      { t: "2026-09-02T11:00:00Z", o: Number.NaN, h: 1.2, l: 1.0, c: 1.15 },
      { t: "2026-09-02T12:00:00Z", o: 1.1, h: 1.2, l: 1.0, c: Number.POSITIVE_INFINITY },
    ]);
    expect(candles).toHaveLength(1);
    expect(candles[0].close).toBe(1.15);
  });

  it("renders native EURUSD chart and never mounts TradingView", async () => {
    render(
      <MemoryRouter>
        <DualChartsPanel
          eurusdTf="1h"
          dxyTf="1h"
          onEurusdTf={() => undefined}
          onDxyTf={() => undefined}
          timeframes={CHART_TIMEFRAMES}
          eurusdQuote={{
            mid: 1.1602,
            status: "live",
            provider: "yahoo_eurusd",
            source: "Yahoo Finance (EURUSD=X)",
            fetched_at: "2026-09-02T12:00:00Z",
          }}
          dxyQuote={{ mid: 99.36, status: "connected", source: "Yahoo Finance (DX-Y.NYB)" }}
          onCreateSignal={() => undefined}
        />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("eurusd-native-chart")).toBeTruthy();
    expect(screen.getByTestId("eurusd-chart-canvas")).toBeTruthy();
    expect(screen.getByTestId("dxy-native-chart")).toBeTruthy();
    expect(screen.queryAllByTestId("tradingview-embed")).toHaveLength(0);
    expect(screen.queryByTestId("tradingview-fallback")).toBeNull();
    expect(document.body.textContent).not.toContain("График TradingView временно недоступен");
    expect(screen.getByTestId("eurusd-quote-line").textContent).toContain("1.16020");
    expect(screen.getByTestId("eurusd-quote-line").textContent).toContain("Yahoo Finance (EURUSD=X)");
    expect(screen.getByTestId("eurusd-quote-line").textContent).not.toMatch(/НБУ/i);
    for (const tf of CHART_TIMEFRAMES) {
      expect(screen.getByTestId(`eurusd-tf-${tf}`)).toBeTruthy();
    }
    await waitFor(() => expect(cryptoFxIntelGet).toHaveBeenCalled());
    expect(
      vi.mocked(cryptoFxIntelGet).mock.calls.some((c) => decodeURIComponent(String(c[0])).includes("EUR/USD")),
    ).toBe(true);
  });

  it("shows retry when candle API fails and keeps the quote", async () => {
    vi.mocked(cryptoFxIntelGet).mockResolvedValue({
      ok: false,
      json: { status: "error", chart_ready: false, bars: [], message: "down" },
    });
    render(
      <MemoryRouter>
        <DualChartsPanel
          eurusdTf="1h"
          dxyTf="1h"
          onEurusdTf={() => undefined}
          onDxyTf={() => undefined}
          timeframes={["1h"] as const}
          eurusdQuote={{ mid: 1.1602, status: "live", provider: "yahoo_eurusd", source: "Yahoo Finance (EURUSD=X)" }}
          dxyQuote={{ mid: 99.36, status: "connected" }}
          onCreateSignal={() => undefined}
        />
      </MemoryRouter>,
    );
    expect(await screen.findByText("Не удалось загрузить график EURUSD")).toBeTruthy();
    expect(screen.getByTestId("eurusd-chart-retry")).toBeTruthy();
    expect(screen.getByTestId("eurusd-quote-line").textContent).toContain("1.16020");
    fireEvent.click(screen.getByTestId("eurusd-chart-retry"));
    await waitFor(() => expect(vi.mocked(cryptoFxIntelGet).mock.calls.length).toBeGreaterThan(1));
  });

  it("does not label live EURUSD as NBU when Yahoo is primary", () => {
    expect(
      eurusdSourceLabel({
        provider: "yahoo_eurusd",
        source: "Yahoo Finance (EURUSD=X)",
      }),
    ).toBe("Yahoo Finance (EURUSD=X)");
    expect(eurusdSourceLabel({ provider: "nbu_cross", source: "НБУ (кросс EUR/USD)" })).toBe(
      "Yahoo Finance (EURUSD=X)",
    );
  });
});
