/**
 * Sprint 50.17 — DXY native intraday; no live-quote fake candle; TF switch isolation.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { DxyNativeChart } from "./DxyNativeChart";
import { applyQuoteToActiveCandle, resetFxChartDiagnostics, type FxCandle } from "./fxNativeChartCore";
import { cryptoFxIntelGet } from "../business-ops/opsApi";

const { series, timeScale, chart } = vi.hoisted(() => {
  const series = { setData: vi.fn(), update: vi.fn(), priceScale: () => ({ applyOptions: vi.fn() }) };
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
    addLineSeries: vi.fn(() => series),
    removeSeries: vi.fn(),
    applyOptions: vi.fn(),
    timeScale: () => timeScale,
    remove: vi.fn(),
  };
  return { series, timeScale, chart };
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

function bars(tf: string, last = Date.parse("2026-09-03T13:00:00Z") / 1000) {
  const step = tf === "1m" ? 60 : tf === "5m" ? 300 : tf === "15m" ? 900 : tf === "4H" ? 14400 : 3600;
  return Array.from({ length: 40 }, (_, i) => {
    const t = last - (39 - i) * step;
    const c = 99.2 + (i % 4) * 0.02;
    return { t: isoFromUnix(t), o: c - 0.01, h: c + 0.03, l: c - 0.03, c };
  });
}

function payload(tf: string, extra: Record<string, unknown> = {}) {
  const rows = bars(tf);
  return {
    ok: true,
    json: {
      status: "connected",
      bars: rows,
      bar_count: rows.length,
      source_resolution: tf === "1h" || tf === "1H" ? "60m" : tf,
      requested_timeframe: tf === "1h" ? "1H" : tf,
      displayed_timeframe: tf === "1h" ? "1H" : tf,
      transformation: "native",
      provider: "yahoo",
      source_symbol: "DX-Y.NYB",
      data_quality: "HEALTHY",
      ...extra,
    },
  };
}

describe("sprint 50.17 DXY intraday", () => {
  beforeEach(() => {
    // @ts-expect-error test stub
    global.ResizeObserver = class {
      observe() {}
      disconnect() {}
      unobserve() {}
    };
    resetFxChartDiagnostics();
    series.setData.mockClear();
    series.update.mockClear();
    vi.mocked(cryptoFxIntelGet).mockImplementation(async (path: string) => {
      const tf = decodeURIComponent(String(path)).match(/timeframe=([^&]+)/)?.[1] || "1H";
      return payload(tf);
    });
  });

  afterEach(() => cleanup());

  it("live quote without history cannot create a fake candle", () => {
    expect(applyQuoteToActiveCandle(null, 99.27, Date.now() / 1000, "15m", "DXY")).toBeNull();
  });

  it("clears the series when DXY TF is unavailable instead of leaving a giant stale candle", async () => {
    vi.mocked(cryptoFxIntelGet).mockImplementation(async (path: string) => {
      const tf = decodeURIComponent(String(path)).match(/timeframe=([^&]+)/)?.[1] || "1H";
      if (tf === "15m") {
        return {
          ok: true,
          json: {
            status: "unavailable",
            source_status: "UNAVAILABLE_AT_SOURCE_RESOLUTION",
            bars: [],
            bar_count: 0,
            requested_timeframe: "15m",
            source_resolution: "15m",
            transformation: "none",
            message: "DXY 15m: источник не предоставляет 15-минутную историю",
          },
        };
      }
      return payload(tf);
    });
    const { rerender } = render(<DxyNativeChart timeframe="1h" liveQuote={{ mid: "99.270", fetched_at: isoFromUnix(1_700_003_600), status: "live" }} />);
    await waitFor(() => expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("ready"));
    rerender(<DxyNativeChart timeframe="15m" liveQuote={{ mid: "99.270", fetched_at: isoFromUnix(1_700_003_600), status: "live" }} />);
    await waitFor(() => expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("unavailable"));
    const last = series.setData.mock.calls.at(-1)?.[0] as FxCandle[];
    expect(Array.isArray(last)).toBe(true);
    expect(last.length).toBe(0);
    expect(series.update).not.toHaveBeenCalled();
    expect(screen.getByTestId("dxy-chart-bars").textContent).toMatch(/15-минутную историю|UNAVAILABLE/);
  });

  it("1h -> 1m -> 5m -> 15m -> 4h does not keep stale candles", async () => {
    const { rerender } = render(<DxyNativeChart timeframe="1h" liveQuote={{ mid: "99.270", fetched_at: isoFromUnix(1_700_003_600), status: "live" }} />);
    for (const tf of ["1m", "5m", "15m", "4h"] as const) {
      rerender(<DxyNativeChart timeframe={tf} liveQuote={{ mid: "99.280", fetched_at: isoFromUnix(1_700_003_700), status: "live" }} />);
      await waitFor(() => expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("ready"));
      const last = series.setData.mock.calls.at(-1)?.[0] as FxCandle[];
      expect(last.length).toBeGreaterThan(1);
      const times = last.map((b) => Number(b.time));
      expect(times).toEqual([...times].sort((a, b) => a - b));
      expect(new Set(times).size).toBe(times.length);
    }
    expect(chart.removeSeries).toHaveBeenCalled();
  });
});
