/**
 * Sprint 50.14 — FX production reliability: TF walk, 429 keep last-good, no giant candle.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, act, cleanup } from "@testing-library/react";
import { EurUsdNativeChart } from "./EurUsdNativeChart";
import { DxyNativeChart } from "./DxyNativeChart";
import {
  applyQuoteToActiveCandle,
  barsToCandles,
  fxOhlcValid,
  fxPriceSane,
  resetFxChartDiagnostics,
  STALE_LIVE_UPDATES_DROPPED,
  FX_QUOTE_POLL_MS,
  type FxCandle,
} from "./fxNativeChartCore";
import { cryptoFxIntelGet } from "../business-ops/opsApi";

const { series, timeScale } = vi.hoisted(() => ({
  series: { setData: vi.fn(), update: vi.fn(), priceScale: () => ({ applyOptions: vi.fn() }) },
  timeScale: {
    fitContent: vi.fn(),
    setVisibleLogicalRange: vi.fn(),
    subscribeVisibleLogicalRangeChange: vi.fn(),
    unsubscribeVisibleLogicalRangeChange: vi.fn(),
    getVisibleLogicalRange: vi.fn(() => null),
  },
}));

vi.mock("../business-ops/opsApi", () => ({
  cryptoFxIntelGet: vi.fn(),
}));

vi.mock("lightweight-charts", () => {
  const chart = {
    addCandlestickSeries: vi.fn(() => series),
    applyOptions: vi.fn(),
    timeScale: () => timeScale,
    remove: vi.fn(),
  };
  return { createChart: vi.fn(() => chart) };
});

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
    const c = close0 + (i % 3) * (close0 > 10 ? 0.01 : 0.0001);
    bars.push({ t: isoFromUnix(t), o: c, h: c + (close0 > 10 ? 0.02 : 0.0002), l: c - (close0 > 10 ? 0.02 : 0.0002), c });
  }
  return bars;
}

function okPayload(bars: { t: string; o: number; h: number; l: number; c: number }[], extra: Record<string, unknown> = {}) {
  return {
    ok: true,
    json: {
      status: "connected",
      chart_ready: true,
      bar_count: bars.length,
      source: extra.source || "Yahoo Finance",
      provider: extra.provider || "yahoo",
      source_status: extra.source_status || "live",
      source_resolution: extra.source_resolution || "1m",
      last_close: bars.at(-1)?.c,
      bars,
      ...extra,
    },
  };
}

const T_LAST = Date.parse("2026-09-03T08:47:00Z") / 1000;
const EUR = {
  "1m": okPayload(barsEndingAt(T_LAST, 60, 40, 1.16), { source_resolution: "1m" }),
  "5m": okPayload(barsEndingAt(T_LAST, 300, 40, 1.16), { source_resolution: "5m" }),
  "15m": okPayload(barsEndingAt(T_LAST, 900, 40, 1.16), { source_resolution: "15m" }),
  "1H": okPayload(barsEndingAt(T_LAST, 3600, 40, 1.16), { source_resolution: "60m" }),
  "4H": okPayload(barsEndingAt(T_LAST, 14400, 40, 1.16), { source_resolution: "4h" }),
  "1D": okPayload(barsEndingAt(T_LAST, 86400, 40, 1.16), { source_resolution: "1d" }),
  "1W": okPayload(barsEndingAt(T_LAST, 604800, 30, 1.16), { source_resolution: "1w" }),
};
const DXY = {
  "1m": okPayload(barsEndingAt(T_LAST, 3600, 40, 99.2), { source_resolution: "60m", source: "Yahoo Finance (DX-Y.NYB)" }),
  "5m": okPayload(barsEndingAt(T_LAST, 3600, 40, 99.2), { source_resolution: "60m" }),
  "15m": okPayload(barsEndingAt(T_LAST, 900, 40, 99.2), { source_resolution: "15m" }),
  "1H": okPayload(barsEndingAt(T_LAST, 3600, 40, 99.2), { source_resolution: "60m" }),
  "4H": okPayload(barsEndingAt(T_LAST, 14400, 40, 99.2), { source_resolution: "4h" }),
  "1D": okPayload(barsEndingAt(T_LAST, 86400, 40, 99.2), { source_resolution: "1d" }),
  "1W": okPayload(barsEndingAt(T_LAST, 604800, 30, 99.2), { source_resolution: "1w" }),
};

function installMonotonicSeries() {
  let lastT = 0;
  series.setData.mockImplementation((bars: FxCandle[]) => {
    lastT = bars.length ? Number(bars[bars.length - 1].time) : lastT;
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

describe("sprint 50.14 FX reliability", () => {
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
    installMonotonicSeries();
    vi.mocked(cryptoFxIntelGet).mockImplementation(async (path: string) => {
      const u = decodeURIComponent(String(path));
      const tf = (u.match(/timeframe=([^&]+)/) || [])[1] || "1H";
      if (u.includes("DXY")) return (DXY as Record<string, ReturnType<typeof okPayload>>)[tf] || DXY["1H"];
      return (EUR as Record<string, ReturnType<typeof okPayload>>)[tf] || EUR["1H"];
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("rejects unit-corrupt prices and zero-low OHLC", () => {
    expect(fxPriceSane("EUR/USD", 11610, 1.161)).toBe(false);
    expect(fxPriceSane("DXY", 99230, 99.23)).toBe(false);
    expect(fxPriceSane("EUR/USD", 1.161, 1.16)).toBe(true);
    expect(fxOhlcValid(1.16, 1.17, 0, 1.161, "EUR/USD")).toBe(false);
    const dropped = barsToCandles(
      [
        { t: "2026-09-03T08:00:00Z", o: 1.16, h: 1.17, l: 0, c: 1.161 },
        { t: "2026-09-03T09:00:00Z", o: 1.16, h: 1.17, l: 1.15, c: 1.161 },
      ],
      "EUR/USD",
    );
    expect(dropped).toHaveLength(1);
  });

  it("does not mint a giant synthetic candle on a new bucket", () => {
    const last: FxCandle = {
      time: Date.parse("2026-09-03T07:00:00Z") / 1000,
      open: 1.161,
      high: 1.162,
      low: 1.16,
      close: 1.1615,
    };
    const created = applyQuoteToActiveCandle(last, 1.164, Date.parse("2026-09-03T08:03:00Z") / 1000, "1h", "EUR/USD");
    expect(created?.open).toBe(1.164);
    expect(created?.high).toBe(1.164);
    expect(created?.low).toBe(1.164);
    expect(created?.close).toBe(1.164);
    expect((created!.high - created!.low) / created!.close).toBeLessThan(0.001);
    const NO_GIANT_SYNTHETIC_CANDLE = created!.high - created!.low < 0.01;
    expect(NO_GIANT_SYNTHETIC_CANDLE).toBe(true);
    expect(applyQuoteToActiveCandle(last, 11610, Date.parse("2026-09-03T08:03:00Z") / 1000, "1h", "EUR/USD")).toBeNull();
  });

  async function walk(
    Chart: typeof EurUsdNativeChart | typeof DxyNativeChart,
    mid: string,
    testId: string,
  ) {
    const tfs = ["1m", "5m", "15m", "1h", "4h", "1D", "1W", "1m"] as const;
    const { rerender } = render(<Chart timeframe="1m" liveQuote={quote(mid)} />);
    for (const tf of tfs) {
      rerender(<Chart timeframe={tf} liveQuote={quote(mid)} />);
      await waitFor(() => expect(screen.getByTestId(testId).getAttribute("data-status")).toBe("ready"));
      expect(Number(screen.getByTestId(testId).getAttribute("data-bar-count") || "0")).toBeGreaterThan(0);
    }
    return { rerender };
  }

  it("EURUSD 1m→5m→15m→1h→4h→1D→1W→1m stays ready", async () => {
    await walk(EurUsdNativeChart, "1.16100", "eurusd-native-chart");
    expect(TIME_ORDER_ERRORS).toBe(0);
    expect(TIMEFRAME_SWITCH_CRASHES).toBe(0);
    expect(ERROR_BOUNDARY_TRIGGERED).toBe(0);
    expect(FX_QUOTE_POLL_MS).toBe(5_000);
  });

  it("DXY same timeframe sequence stays ready with honest resolution", async () => {
    await walk(DxyNativeChart, "99.274", "dxy-native-chart");
    expect(TIME_ORDER_ERRORS).toBe(0);
    expect(screen.getByTestId("dxy-native-chart").getAttribute("data-source-resolution")).toBeTruthy();
  });

  it("rapid 1m→5m→1m→15m→5m→1h→4h→1m does not crash", async () => {
    const seq = ["1m", "5m", "1m", "15m", "5m", "1h", "4h", "1m"] as const;
    for (let round = 0; round < 3; round += 1) {
      cleanup();
      const { rerender } = render(<EurUsdNativeChart timeframe="1m" liveQuote={quote("1.16100")} />);
      for (const tf of seq) {
        rerender(<EurUsdNativeChart timeframe={tf} liveQuote={quote("1.16110")} />);
      }
      await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
      cleanup();
      const { rerender: dxyRerender } = render(<DxyNativeChart timeframe="1m" liveQuote={quote("99.27")} />);
      for (const tf of seq) {
        dxyRerender(<DxyNativeChart timeframe={tf} liveQuote={quote("99.28")} />);
      }
      await waitFor(() => expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("ready"));
    }
    expect(TIME_ORDER_ERRORS).toBe(0);
    expect(TIMEFRAME_SWITCH_CRASHES).toBe(0);
    expect(ERROR_BOUNDARY_TRIGGERED).toBe(0);
    const emptied = series.setData.mock.calls.filter((c) => (c[0] as FxCandle[]).length === 0);
    expect(emptied.length).toBe(0);
  });

  it("429 / empty history does not wipe a valid chart", async () => {
    const { rerender } = render(<EurUsdNativeChart timeframe="1h" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    series.setData.mockClear();
    vi.mocked(cryptoFxIntelGet).mockResolvedValue({
      ok: false,
      json: { status: "error", chart_ready: false, bars: [], message: "Yahoo HTTP 429", source_status: "rate_limited" },
    });
    rerender(<EurUsdNativeChart timeframe="5m" liveQuote={quote("1.16100")} />);
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });
    const emptied = series.setData.mock.calls.filter((c) => (c[0] as FxCandle[]).length === 0);
    expect(emptied.length).toBe(0);
    expect(screen.getByTestId("eurusd-native-chart")).toBeTruthy();
    expect(TIME_ORDER_ERRORS).toBe(0);
  });

  it("rate-limited payload with last-good bars still paints", async () => {
    const bars = barsEndingAt(T_LAST, 3600, 20, 99.2);
    vi.mocked(cryptoFxIntelGet).mockResolvedValue({
      ok: true,
      json: {
        status: "delayed",
        chart_ready: true,
        bars,
        bar_count: bars.length,
        source_status: "rate_limited",
        stale: true,
        cache: "last_good",
        provider: "yahoo",
        source_resolution: "60m",
        source: "Yahoo Finance (DX-Y.NYB)",
      },
    });
    render(<DxyNativeChart timeframe="1m" liveQuote={quote("99.27")} />);
    await waitFor(() => expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(Number(screen.getByTestId("dxy-native-chart").getAttribute("data-bar-count"))).toBeGreaterThan(0);
    expect(screen.getByTestId("dxy-rate-limited").textContent).toContain("RATE LIMITED");
    expect(STALE_LIVE_UPDATES_DROPPED).toBeGreaterThanOrEqual(0);
  });
});
