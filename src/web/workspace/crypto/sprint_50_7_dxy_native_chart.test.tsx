/**
 * Sprint 50.7 — DXY native Lightweight Charts (no TVC:DXY popup).
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { barsToCandles, normalizeCandlesTimeframe } from "./DxyNativeChart";
import { DualChartsPanel } from "./paperTradingPanels";
import { tvSymbolFor } from "./TradingViewEmbed";

vi.mock("../business-ops/opsApi", () => ({
  cryptoFxIntelGet: vi.fn(async () => ({
    ok: true,
    json: {
      status: "connected",
      chart_ready: true,
      bar_count: 3,
      source: "Yahoo Finance (DX-Y.NYB)",
      provider: "yahoo",
      last_close: 99.5,
      bars: [
        { t: "2026-08-12T10:00:00+00:00", o: 99.1, h: 99.4, l: 99.0, c: 99.2 },
        { t: "2026-08-12T11:00:00+00:00", o: 99.2, h: 99.6, l: 99.1, c: 99.5 },
        { t: "2026-08-12T12:00:00+00:00", o: 99.5, h: 99.7, l: 99.3, c: 99.4 },
      ],
    },
  })),
}));

vi.mock("lightweight-charts", () => {
  const series = { setData: vi.fn() };
  const chart = {
    addCandlestickSeries: vi.fn(() => series),
    applyOptions: vi.fn(),
    timeScale: () => ({ fitContent: vi.fn() }),
    remove: vi.fn(),
  };
  return {
    createChart: vi.fn(() => chart),
  };
});

describe("sprint 50.7 DXY native chart", () => {
  beforeEach(() => {
    // jsdom ResizeObserver stub
    // @ts-expect-error test stub
    global.ResizeObserver = class {
      observe() {}
      disconnect() {}
      unobserve() {}
    };
  });

  it("normalizes candle timeframes for API", () => {
    expect(normalizeCandlesTimeframe("1h")).toBe("1H");
    expect(normalizeCandlesTimeframe("15m")).toBe("15m");
    expect(normalizeCandlesTimeframe("4H")).toBe("4H");
    expect(normalizeCandlesTimeframe("1m")).toBe("1m");
    expect(normalizeCandlesTimeframe("5m")).toBe("5m");
    expect(normalizeCandlesTimeframe("1W")).toBe("1W");
  });

  it("maps bars to ascending lightweight candles", () => {
    const candles = barsToCandles([
      { t: "2026-08-12T10:00:00Z", o: 1, h: 2, l: 0.5, c: 1.5 },
      { t: "2026-08-12T11:00:00Z", o: 1.5, h: 2.5, l: 1.4, c: 2 },
    ]);
    expect(candles).toHaveLength(2);
    expect(Number(candles[1].time)).toBeGreaterThan(Number(candles[0].time));
  });

  it("legacy tvSymbolFor still documents TVC:DXY but DualCharts does not embed it for DXY", () => {
    expect(tvSymbolFor("DXY")).toBe("TVC:DXY");
    render(
      <MemoryRouter>
        <DualChartsPanel
          eurusdTf="1h"
          dxyTf="1h"
          onEurusdTf={() => undefined}
          onDxyTf={() => undefined}
          timeframes={["15m", "1h", "4h", "1D"] as const}
          eurusdQuote={{ mid: 1.1, status: "connected" }}
          dxyQuote={{ mid: 99.5, status: "connected", source: "Yahoo Finance (DX-Y.NYB)" }}
          onCreateSignal={() => undefined}
        />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("dxy-native-chart")).toBeTruthy();
    expect(screen.getByTestId("dxy-native-chart").getAttribute("data-engine")).toBe("lightweight-charts");
    expect(screen.getByTestId("eurusd-native-chart")).toBeTruthy();
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-engine")).toBe("lightweight-charts");
    expect(screen.queryAllByTestId("tradingview-embed")).toHaveLength(0);
    expect(document.body.textContent).not.toContain("График TradingView временно недоступен");
  });

  it("timeframe buttons call onDxyTf", () => {
    const onDxyTf = vi.fn();
    render(
      <MemoryRouter>
        <DualChartsPanel
          eurusdTf="1h"
          dxyTf="1h"
          onEurusdTf={() => undefined}
          onDxyTf={onDxyTf}
          timeframes={["15m", "1h", "4h", "1D"] as const}
          eurusdQuote={{ mid: 1.1, status: "connected" }}
          dxyQuote={{ mid: 99.5, status: "connected" }}
          onCreateSignal={() => undefined}
        />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId("dxy-tf-4h"));
    expect(onDxyTf).toHaveBeenCalledWith("4h");
    expect(screen.getByTestId("chart-signal-EUR/USD").textContent).toContain("Создать сигнал");
    expect(screen.getByTestId("chart-analysis-EUR/USD").textContent).toContain("К анализу");
    expect(screen.getByTestId("chart-paper-EUR/USD").textContent).toContain("Бумажная торговля");
  });

  it("shows live DXY quote line", () => {
    render(
      <MemoryRouter>
        <DualChartsPanel
          eurusdTf="1h"
          dxyTf="1h"
          onEurusdTf={() => undefined}
          onDxyTf={() => undefined}
          timeframes={["1h"] as const}
          eurusdQuote={{ mid: 1.1, status: "connected" }}
          dxyQuote={{ mid: 99.87, status: "connected", source: "Yahoo" }}
          onCreateSignal={() => undefined}
        />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("dxy-quote-line").textContent).toContain("99.870");
    expect(screen.getByTestId("dxy-quote-line").textContent).not.toMatch(/\bNaN\b/);
    expect(screen.getByTestId("eurusd-quote-line").textContent).toContain("1.1000");
    expect(screen.getByTestId("eurusd-quote-line").textContent).not.toMatch(/\bNaN\b/);
  });

  it("does not render NaN when quote mid is invalid", () => {
    render(
      <MemoryRouter>
        <DualChartsPanel
          eurusdTf="1h"
          dxyTf="1h"
          onEurusdTf={() => undefined}
          onDxyTf={() => undefined}
          timeframes={["1h"] as const}
          eurusdQuote={{ mid: Number.NaN, status: "connected" }}
          dxyQuote={{ mid: "NaN", status: "connected" }}
          onCreateSignal={() => undefined}
        />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("eurusd-quote-line").textContent).not.toMatch(/\bNaN\b/);
    expect(screen.getByTestId("dxy-quote-line").textContent).not.toMatch(/\bNaN\b/);
  });
});
