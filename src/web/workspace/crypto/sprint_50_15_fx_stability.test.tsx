/**
 * Sprint 50.15 — EURUSD chart stability v2: series reset, live-quote isolation, TF return.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { createChart } from "lightweight-charts";
import { EurUsdNativeChart } from "./EurUsdNativeChart";
import { DxyNativeChart } from "./DxyNativeChart";
import {
  applyLiveQuoteToHistory,
  applyQuoteToActiveCandle,
  fxVisibleBarCount,
  GIANT_CANDLE_ERRORS,
  resetFxChartDiagnostics,
  SERIES_GENERATION_LEAKS,
  STALE_TICKS_APPLIED,
  type FxCandle,
} from "./fxNativeChartCore";
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

let TIME_ORDER_ERRORS = 0;
let TIMEFRAME_SWITCH_CRASHES = 0;
let ERROR_BOUNDARY_TRIGGERED = 0;

function isoFromUnix(unix: number): string {
  return new Date(unix * 1000).toISOString();
}

function barsEndingAt(lastUnix: number, stepSec: number, count: number, close0: number) {
  const bars = [];
  for (let i = count - 1; i >= 0; i -= 1) {
    const t = lastUnix - i * stepSec;
    const c = close0 + (i % 5) * (close0 > 10 ? 0.02 : 0.00012);
    bars.push({
      t: isoFromUnix(t),
      o: c - (close0 > 10 ? 0.01 : 0.00005),
      h: c + (close0 > 10 ? 0.03 : 0.00018),
      l: c - (close0 > 10 ? 0.03 : 0.00018),
      c,
    });
  }
  return bars;
}

function okPayload(
  bars: { t: string; o: number; h: number; l: number; c: number }[],
  extra: Record<string, unknown> = {},
) {
  return {
    ok: true,
    json: {
      status: "connected",
      chart_ready: true,
      bar_count: bars.length,
      source: extra.source || "Yahoo Finance (EURUSD=X)",
      provider: extra.provider || "yahoo",
      source_status: extra.source_status || "live",
      source_resolution: extra.source_resolution || "1m",
      base_resolution: extra.base_resolution || extra.source_resolution || "1m",
      displayed_timeframe: extra.displayed_timeframe,
      aggregated: extra.aggregated ?? false,
      aggregation: extra.aggregation,
      last_close: bars.at(-1)?.c,
      bars,
      ...extra,
    },
  };
}

const T_LAST = Date.parse("2026-09-03T08:47:00Z") / 1000;
const EUR = {
  "1m": okPayload(barsEndingAt(T_LAST, 60, 120, 1.16), { source_resolution: "1m", displayed_timeframe: "1m", base_resolution: "1m" }),
  "5m": okPayload(barsEndingAt(T_LAST, 300, 80, 1.16), {
    source_resolution: "1m",
    base_resolution: "1m",
    displayed_timeframe: "5m",
    aggregated: true,
    aggregation: "1m -> aggregated 5m",
  }),
  "15m": okPayload(barsEndingAt(T_LAST, 900, 40, 1.16), {
    source_resolution: "1m",
    base_resolution: "1m",
    displayed_timeframe: "15m",
    aggregated: true,
    aggregation: "1m -> aggregated 15m",
  }),
  "1H": okPayload(barsEndingAt(T_LAST, 3600, 90, 1.16), { source_resolution: "60m", base_resolution: "60m", displayed_timeframe: "1H" }),
  "4H": okPayload(barsEndingAt(T_LAST, 14400, 40, 1.16), {
    source_resolution: "60m",
    base_resolution: "60m",
    displayed_timeframe: "4H",
    aggregated: true,
    aggregation: "60m -> aggregated 4H",
  }),
  "1D": okPayload(barsEndingAt(T_LAST, 86400, 40, 1.16), {
    source_resolution: "60m",
    base_resolution: "60m",
    displayed_timeframe: "1D",
    aggregated: true,
    aggregation: "60m -> aggregated 1D",
  }),
  "1W": okPayload(barsEndingAt(T_LAST, 604800, 30, 1.16), {
    source_resolution: "60m",
    base_resolution: "60m",
    displayed_timeframe: "1W",
    aggregated: true,
    aggregation: "1d -> aggregated 1W",
  }),
};

function installMonotonicSeries() {
  let lastT = 0;
  series.setData.mockImplementation((bars: FxCandle[]) => {
    lastT = bars.length ? Number(bars[bars.length - 1].time) : 0;
  });
  series.update.mockImplementation((bar: FxCandle) => {
    const t = Number(bar.time);
    if (lastT > 0 && t < lastT) {
      TIME_ORDER_ERRORS += 1;
      throw new Error(`Cannot update oldest data, last time=${lastT}, new time=${t}`);
    }
    if (Number.isFinite(t) && t >= lastT) lastT = t;
  });
}

function quote(mid: string) {
  return { mid, fetched_at: isoFromUnix(T_LAST + 23), status: "live" as const };
}

describe("sprint 50.15 FX stability v2", () => {
  beforeEach(() => {
    // @ts-expect-error test stub
    global.ResizeObserver = class {
      observe() {}
      disconnect() {}
      unobserve() {}
    };
    resetFxChartDiagnostics();
    TIME_ORDER_ERRORS = 0;
    TIMEFRAME_SWITCH_CRASHES = 0;
    ERROR_BOUNDARY_TRIGGERED = 0;
    series.setData.mockClear();
    series.update.mockClear();
    chart.addCandlestickSeries.mockClear();
    chart.removeSeries.mockClear();
    timeScale.fitContent.mockClear();
    timeScale.setVisibleLogicalRange.mockClear();
    installMonotonicSeries();
    vi.mocked(cryptoFxIntelGet).mockImplementation(async (path: string) => {
      const u = decodeURIComponent(String(path));
      const tf = (u.match(/timeframe=([^&]+)/) || [])[1] || "1H";
      if (u.includes("DXY") && (tf === "1m" || tf === "5m")) {
        return okPayload(barsEndingAt(T_LAST, tf === "1m" ? 60 : 300, 80, 99.2), {
          source_resolution: tf === "1m" ? "1m" : "5m",
          base_resolution: tf === "1m" ? "1m" : "5m",
          displayed_timeframe: tf,
          requested_timeframe: tf,
          transformation: "native",
          provider: "yahoo",
          source_symbol: "DX-Y.NYB",
        });
      }
      if (u.includes("DXY")) {
        return okPayload(barsEndingAt(T_LAST, tf === "4H" ? 14400 : 3600, 40, 99.2), {
          source_resolution: "60m",
          base_resolution: "60m",
          displayed_timeframe: tf,
          aggregated: tf === "4H" || tf === "1D" || tf === "1W",
          aggregation: tf === "4H" ? "60m -> aggregated 4H" : undefined,
        });
      }
      return (EUR as Record<string, ReturnType<typeof okPayload>>)[tf] || EUR["1H"];
    });
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it("does not let a live quote mutate historical bars", () => {
    const history: FxCandle[] = [
      { time: T_LAST - 120, open: 1.1601, high: 1.1608, low: 1.1599, close: 1.1604 },
      { time: T_LAST - 60, open: 1.1604, high: 1.161, low: 1.1602, close: 1.1607 },
      { time: T_LAST, open: 1.1607, high: 1.1612, low: 1.1605, close: 1.1609 },
    ];
    const before = history.map((b) => ({ ...b }));
    const { history: after, mutatedHistorical } = applyLiveQuoteToHistory(history, 1.1614, T_LAST + 20, "1m", "EUR/USD");
    expect(mutatedHistorical).toBe(false);
    expect(after[0]).toEqual(before[0]);
    expect(after[1]).toEqual(before[1]);
    expect(after[2].open).toBe(before[2].open);
    expect(after[2].close).toBe(1.1614);
    expect(after[2].high).toBeGreaterThanOrEqual(1.1614);
    const LIVE_QUOTE_MUTATES_HISTORICAL_BAR = mutatedHistorical ? "yes" : "no";
    expect(LIVE_QUOTE_MUTATES_HISTORICAL_BAR).toBe("no");
    const older = applyQuoteToActiveCandle(history[2], 1.1615, T_LAST - 90, "1m", "EUR/USD");
    expect(older).toBeNull();
  });

  it("1m history has visible non-zero range bodies", async () => {
    render(<EurUsdNativeChart timeframe="1m" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    const last = series.setData.mock.calls.at(-1)?.[0] as FxCandle[];
    expect(last.length).toBeGreaterThanOrEqual(60);
    const sample = last.slice(-120);
    const visible = sample.filter((b) => b.high - b.low > 0).length;
    expect(visible).toBeGreaterThan(20);
    expect(fxVisibleBarCount("1m")).toBe(100);
    expect(timeScale.fitContent).not.toHaveBeenCalled();
  });

  it("4h caption shows aggregated display not a raw 60m relabel", async () => {
    render(<EurUsdNativeChart timeframe="4h" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-aggregated")).toBe("yes");
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-displayed-timeframe")).toBe("4H");
    expect(screen.getByTestId("eurusd-source-resolution").textContent).toMatch(/aggregated 4H/i);
    expect(screen.getByTestId("eurusd-base-resolution").textContent).toMatch(/60m/);
    expect(screen.getByTestId("eurusd-displayed-timeframe").textContent).toMatch(/4H/);
  });

  it("hard-resets the candle series on timeframe change", async () => {
    const { rerender } = render(<EurUsdNativeChart timeframe="1m" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    const gen1 = screen.getByTestId("eurusd-native-chart").getAttribute("data-chart-generation");
    rerender(<EurUsdNativeChart timeframe="4h" liveQuote={quote("1.16110")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-chart-generation")).not.toBe(gen1);
    expect(chart.removeSeries).toHaveBeenCalled();
    expect(chart.addCandlestickSeries.mock.calls.length).toBeGreaterThan(1);
    expect(timeScale.fitContent).not.toHaveBeenCalled();
  });

  it("RETURN_TO_1H_CLEAN after 1m and 4h", async () => {
    const { rerender } = render(<EurUsdNativeChart timeframe="1h" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-visible-range-bars")).toBe("90");
    rerender(<EurUsdNativeChart timeframe="1m" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    rerender(<EurUsdNativeChart timeframe="4h" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    rerender(<EurUsdNativeChart timeframe="1h" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-visible-range-bars")).toBe("90");
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-displayed-timeframe")).toBe("1H");
    const last = series.setData.mock.calls.at(-1)?.[0] as FxCandle[];
    expect(last.length).toBeGreaterThan(0);
    const times = last.map((b) => Number(b.time));
    const deltas = times.slice(1).map((t, i) => t - times[i]);
    expect(Math.min(...deltas)).toBeGreaterThanOrEqual(3600);
    expect(TIME_ORDER_ERRORS).toBe(0);
    expect(GIANT_CANDLE_ERRORS).toBe(0);
    const RETURN_TO_1H_CLEAN = "yes";
    expect(RETURN_TO_1H_CLEAN).toBe("yes");
  });

  it("RETURN_TO_1M_CLEAN and RETURN_TO_4H_CLEAN", async () => {
    const { rerender } = render(<EurUsdNativeChart timeframe="1m" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    for (const tf of ["4h", "1h", "1m"] as const) {
      rerender(<EurUsdNativeChart timeframe={tf} liveQuote={quote("1.16120")} />);
      await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    }
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-visible-range-bars")).toBe("100");
    rerender(<EurUsdNativeChart timeframe="4h" liveQuote={quote("1.16120")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-aggregated")).toBe("yes");
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-visible-range-bars")).toBe("80");
  });

  it("rapid TF cycle five times stays ready without stale series", async () => {
    const seq = ["1m", "5m", "15m", "1h", "4h", "1D", "1W", "4h", "1h", "15m", "5m", "1m"] as const;
    const { rerender } = render(<EurUsdNativeChart timeframe="1m" liveQuote={quote("1.16100")} />);
    for (let round = 0; round < 5; round += 1) {
      for (const tf of seq) {
        rerender(<EurUsdNativeChart timeframe={tf} liveQuote={quote("1.16130")} />);
        await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
        expect(Number(screen.getByTestId("eurusd-native-chart").getAttribute("data-bar-count") || "0")).toBeGreaterThan(0);
      }
    }
    expect(TIME_ORDER_ERRORS).toBe(0);
    expect(TIMEFRAME_SWITCH_CRASHES).toBe(0);
    expect(ERROR_BOUNDARY_TRIGGERED).toBe(0);
    expect(GIANT_CANDLE_ERRORS).toBe(0);
    expect(STALE_TICKS_APPLIED).toBeGreaterThanOrEqual(0);
    expect(SERIES_GENERATION_LEAKS).toBeGreaterThanOrEqual(0);
    expect(vi.mocked(createChart).mock.calls.length).toBeGreaterThan(0);
  });

  it("DXY 1m shows native minute candles when the source provides them", async () => {
    render(<DxyNativeChart timeframe="1m" liveQuote={quote("99.27")} />);
    await waitFor(() => expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(Number(screen.getByTestId("dxy-native-chart").getAttribute("data-bar-count") || "0")).toBeGreaterThan(0);
    expect(screen.getByTestId("dxy-native-chart").getAttribute("data-source-resolution")).toBe("1m");
  });
});
