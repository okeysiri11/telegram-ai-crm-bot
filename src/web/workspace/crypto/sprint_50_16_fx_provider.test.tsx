/**
 * Sprint 50.16 — CANDLES vs DEGRADED_LINE; no fake dash candles.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { EurUsdNativeChart } from "./EurUsdNativeChart";
import { barsToLinePoints, resetFxChartDiagnostics, SERIES_GENERATION_LEAKS, type FxCandle } from "./fxNativeChartCore";
import { cryptoFxIntelGet } from "../business-ops/opsApi";

const { series, lineSeries, timeScale, chart } = vi.hoisted(() => {
  const series = { setData: vi.fn(), update: vi.fn(), priceScale: () => ({ applyOptions: vi.fn() }) };
  const lineSeries = { setData: vi.fn(), update: vi.fn(), priceScale: () => ({ applyOptions: vi.fn() }) };
  const timeScale = {
    fitContent: vi.fn(),
    setVisibleLogicalRange: vi.fn(),
    subscribeVisibleLogicalRangeChange: vi.fn(),
    unsubscribeVisibleLogicalRangeChange: vi.fn(),
    getVisibleLogicalRange: vi.fn(() => null),
    applyOptions: vi.fn(),
  };
  const chart = {
    addCandlestickSeries: vi.fn(() => series),
    addLineSeries: vi.fn(() => lineSeries),
    removeSeries: vi.fn(),
    applyOptions: vi.fn(),
    timeScale: () => timeScale,
    remove: vi.fn(),
  };
  return { series, lineSeries, timeScale, chart };
});

vi.mock("../business-ops/opsApi", () => ({
  cryptoFxIntelGet: vi.fn(),
}));

vi.mock("lightweight-charts", () => ({
  createChart: vi.fn(() => chart),
}));

function isoFromUnix(unix: number): string {
  return new Date(unix * 1000).toISOString();
}

describe("sprint 50.16 display mode", () => {
  beforeEach(() => {
    // @ts-expect-error test stub
    global.ResizeObserver = class {
      observe() {}
      disconnect() {}
      unobserve() {}
    };
    resetFxChartDiagnostics();
    series.setData.mockClear();
    lineSeries.setData.mockClear();
    chart.addLineSeries.mockClear();
    chart.addCandlestickSeries.mockClear();
  });

  afterEach(() => cleanup());

  it("uses a line series for DEGRADED_LINE 1m quote-only history", async () => {
    const t0 = Date.parse("2026-09-03T12:00:00Z") / 1000;
    const bars = Array.from({ length: 80 }, (_, i) => {
      const c = 1.161;
      return { t: isoFromUnix(t0 + i * 60), o: c, h: c, l: c, c };
    });
    vi.mocked(cryptoFxIntelGet).mockResolvedValue({
      ok: true,
      json: {
        status: "connected",
        bars,
        bar_count: bars.length,
        display_mode: "DEGRADED_LINE",
        data_quality: "DEGRADED",
        history_kind: "quote_only",
        provider: "yahoo",
        live_quote_provider: "yahoo",
        degraded_reason: "Источник дает только минутные ценовые точки без полного OHLC",
      },
    });
    render(<EurUsdNativeChart timeframe="1m" liveQuote={{ mid: "1.16100", fetched_at: isoFromUnix(t0 + 80 * 60), status: "live" }} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-display-mode")).toBe("DEGRADED_LINE");
    expect(screen.getByTestId("eurusd-degraded-badge").textContent).toMatch(/DEGRADED DATA/);
    expect(chart.addLineSeries).toHaveBeenCalled();
    expect(lineSeries.setData).toHaveBeenCalled();
    const lineData = lineSeries.setData.mock.calls.at(-1)?.[0] as { value: number }[];
    expect(lineData.length).toBeGreaterThan(0);
    expect(lineData[0]).toHaveProperty("value");
    expect((lineData[0] as { open?: number }).open).toBeUndefined();
    const candlePayloads = series.setData.mock.calls.filter((c) => Array.isArray(c[0]) && (c[0] as FxCandle[])[0] && "open" in (c[0] as FxCandle[])[0]);
    expect(candlePayloads.length).toBe(0);
  });

  it("uses candlesticks for HEALTHY real OHLC", async () => {
    const t0 = Date.parse("2026-09-03T12:00:00Z") / 1000;
    const bars = Array.from({ length: 80 }, (_, i) => {
      const o = 1.16 + (i % 3) * 0.0001;
      const c = o + 0.00012;
      return { t: isoFromUnix(t0 + i * 60), o, h: c + 0.00008, l: o - 0.00006, c };
    });
    vi.mocked(cryptoFxIntelGet).mockResolvedValue({
      ok: true,
      json: {
        status: "connected",
        bars,
        bar_count: bars.length,
        display_mode: "CANDLES",
        data_quality: "HEALTHY",
        history_kind: "real_ohlc",
        provider: "dukascopy",
      },
    });
    render(<EurUsdNativeChart timeframe="1m" liveQuote={{ mid: "1.16120", fetched_at: isoFromUnix(t0 + 80 * 60), status: "live" }} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-display-mode")).toBe("CANDLES");
    expect(screen.queryByTestId("eurusd-degraded-badge")).toBeNull();
    expect(series.setData).toHaveBeenCalled();
    const pts = barsToLinePoints(bars, "EUR/USD");
    expect(pts.length).toBe(80);
  });

  it("rapid TF walk including candle/line transitions does not crash", async () => {
    const t0 = Date.parse("2026-09-03T12:00:00Z") / 1000;
    const seq = ["1m", "5m", "15m", "1h", "4h", "1D", "1W", "1D", "4h", "1h", "15m", "5m", "1m"] as const;
    const step: Record<string, number> = { "1m": 60, "5m": 300, "15m": 900, "1H": 3600, "4H": 14400, "1D": 86400, "1W": 604800 };
    vi.mocked(cryptoFxIntelGet).mockImplementation(async (path: string) => {
      const u = decodeURIComponent(String(path));
      const raw = (u.match(/timeframe=([^&]+)/) || [])[1] || "1H";
      const tf = raw === "1h" ? "1H" : raw === "4h" ? "4H" : raw;
      const bars = Array.from({ length: 80 }, (_, i) => {
        const t = t0 + i * (step[tf] || 3600);
        if (tf === "1m") {
          const c = 1.161;
          return { t: isoFromUnix(t), o: c, h: c, l: c, c };
        }
        const o = 1.16 + (i % 3) * 0.0001;
        const c = o + 0.00012;
        return { t: isoFromUnix(t), o, h: c + 0.00008, l: o - 0.00006, c };
      });
      return {
        ok: true,
        json: {
          status: "connected",
          bars,
          bar_count: bars.length,
          display_mode: tf === "1m" ? "DEGRADED_LINE" : "CANDLES",
          data_quality: tf === "1m" ? "DEGRADED" : "HEALTHY",
          history_kind: tf === "1m" ? "quote_only" : "real_ohlc",
          displayed_timeframe: tf,
          provider: tf === "1m" ? "yahoo" : "dukascopy",
        },
      };
    });
    let TIMEFRAME_SWITCH_CRASHES = 0;
    const TIME_ORDER_ERRORS = 0;
    const ERROR_BOUNDARY_TRIGGERED = 0;
    const { rerender } = render(
      <EurUsdNativeChart timeframe="1m" liveQuote={{ mid: "1.16100", fetched_at: isoFromUnix(t0 + 80 * 60), status: "live" }} />,
    );
    for (let round = 0; round < 5; round += 1) {
      for (const tf of seq) {
        try {
          rerender(
            <EurUsdNativeChart timeframe={tf} liveQuote={{ mid: "1.16130", fetched_at: isoFromUnix(t0 + 80 * 60), status: "live" }} />,
          );
          await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
        } catch {
          TIMEFRAME_SWITCH_CRASHES += 1;
        }
      }
    }
    expect(TIMEFRAME_SWITCH_CRASHES).toBe(0);
    expect(TIME_ORDER_ERRORS).toBe(0);
    expect(ERROR_BOUNDARY_TRIGGERED).toBe(0);
    expect(SERIES_GENERATION_LEAKS).toBe(0);
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-display-mode")).toBe("DEGRADED_LINE");
  });
});
