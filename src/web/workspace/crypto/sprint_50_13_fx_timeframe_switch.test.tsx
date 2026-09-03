/**
 * Sprint 50.13 — timeframe switch must not crash Lightweight Charts
 * (stale live tick + mixed/old timestamps).
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import type { ReactElement } from "react";
import { EurUsdNativeChart } from "./EurUsdNativeChart";
import { DxyNativeChart } from "./DxyNativeChart";
import {
  applyQuoteToActiveCandle,
  barsToCandles,
  candleBucketUnix,
  FX_HISTORY_DUPLICATES_DROPPED,
  FX_INVALID_TIMESTAMPS_DROPPED,
  lastSeriesTimestampOf,
  normalizeChartTime,
  normalizeHistoryCandles,
  resetFxChartDiagnostics,
  safeUpdateCandlestick,
  STALE_LIVE_UPDATES_DROPPED,
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
  return {
    createChart: vi.fn(() => chart),
  };
});

const T_1M_LAST = Date.parse("2026-09-03T08:47:00Z") / 1000;
const T_QUOTE = Date.parse("2026-09-03T08:47:23Z") / 1000;
const T_5M_BUCKET = Date.parse("2026-09-03T08:45:00Z") / 1000;

function isoFromUnix(unix: number): string {
  return new Date(unix * 1000).toISOString();
}

function barsEndingAt(lastUnix: number, stepSec: number, count: number) {
  const bars = [];
  for (let i = count - 1; i >= 0; i -= 1) {
    const t = lastUnix - i * stepSec;
    const c = 1.16 + (i % 3) * 0.0001;
    bars.push({ t: isoFromUnix(t), o: c, h: c + 0.0002, l: c - 0.0002, c });
  }
  return bars;
}

function payload(bars: { t: string; o: number; h: number; l: number; c: number }[], source: string) {
  return {
    ok: true,
    json: {
      status: "connected",
      chart_ready: true,
      bar_count: bars.length,
      source,
      last_close: bars.at(-1)?.c,
      bars,
    },
  };
}

const eurusd1m = payload(barsEndingAt(T_1M_LAST, 60, 12), "Yahoo Finance (EURUSD=X)");
const eurusd5m = payload(barsEndingAt(T_5M_BUCKET, 300, 8), "Yahoo Finance (EURUSD=X)");
const eurusd15m = payload(barsEndingAt(Date.parse("2026-09-03T08:30:00Z") / 1000, 900, 6), "Yahoo Finance (EURUSD=X)");
const eurusd1h = payload(barsEndingAt(Date.parse("2026-09-03T08:00:00Z") / 1000, 3600, 6), "Yahoo Finance (EURUSD=X)");
const eurusd4h = payload(barsEndingAt(Date.parse("2026-09-03T08:00:00Z") / 1000, 14400, 4), "Yahoo Finance (EURUSD=X)");
const eurusd1d = payload(barsEndingAt(Date.parse("2026-09-03T00:00:00Z") / 1000, 86400, 5), "Yahoo Finance (EURUSD=X)");
const eurusd1w = payload(barsEndingAt(Date.parse("2026-08-31T00:00:00Z") / 1000, 604800, 4), "Yahoo Finance (EURUSD=X)");

const dxyHourly = payload(
  barsEndingAt(Date.parse("2026-09-03T08:00:00Z") / 1000, 3600, 10).map((b) => ({
    ...b,
    o: 99.2,
    h: 99.4,
    l: 99.1,
    c: 99.27,
  })),
  "Yahoo Finance (DX-Y.NYB)",
);

function installMonotonicSeries() {
  let lastT = 0;
  series.setData.mockImplementation((bars: FxCandle[]) => {
    lastT = bars.length ? Number(bars[bars.length - 1].time) : 0;
  });
  series.update.mockImplementation((bar: FxCandle) => {
    const time = bar.time as unknown;
    if (time != null && typeof time === "object") {
      throw new Error(`Cannot update oldest data, last time=${String(time)}, new time=${String(time)}`);
    }
    const t = Number(bar.time);
    if (lastT > 0 && t < lastT) {
      throw new Error(`Cannot update oldest data, last time=${lastT}, new time=${t}`);
    }
    if (Number.isFinite(t) && t >= lastT) lastT = t;
  });
}

function quote(mid: string, unix = T_QUOTE) {
  return { mid, fetched_at: isoFromUnix(unix), status: "live" as const };
}

describe("sprint 50.13 timeframe switch guard", () => {
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
    timeScale.setVisibleLogicalRange.mockClear();
    installMonotonicSeries();
    vi.mocked(cryptoFxIntelGet).mockImplementation(async (path: string) => {
      const u = decodeURIComponent(String(path));
      if (u.includes("DXY")) return dxyHourly;
      if (u.includes("timeframe=1m")) return eurusd1m;
      if (u.includes("timeframe=5m")) return eurusd5m;
      if (u.includes("timeframe=15m")) return eurusd15m;
      if (u.includes("timeframe=1H")) return eurusd1h;
      if (u.includes("timeframe=4H")) return eurusd4h;
      if (u.includes("timeframe=1D")) return eurusd1d;
      if (u.includes("timeframe=1W")) return eurusd1w;
      return eurusd1h;
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("normalizes only numeric unix seconds and rejects junk", () => {
    expect(normalizeChartTime(1_757_000_000)).toBe(1_757_000_000);
    expect(normalizeChartTime(1_757_000_000_000)).toBe(1_757_000_000);
    expect(normalizeChartTime("2026-09-03T08:47:00Z")).toBe(T_1M_LAST);
    expect(normalizeChartTime({ year: 2026, month: 9, day: 3 })).toBe(Date.parse("2026-09-03T00:00:00Z") / 1000);
    expect(normalizeChartTime(Number.NaN)).toBeNull();
    expect(normalizeChartTime(undefined)).toBeNull();
    expect(normalizeChartTime(null)).toBeNull();
    expect(normalizeChartTime({})).toBeNull();
  });

  it("sorts history, drops duplicates, and keeps strictly increasing times", () => {
    const candles = barsToCandles([
      { t: "2026-09-03T08:47:00Z", o: 1.16, h: 1.17, l: 1.15, c: 1.161 },
      { t: "2026-09-03T08:45:00Z", o: 1.15, h: 1.16, l: 1.14, c: 1.16 },
      { t: "2026-09-03T08:47:00Z", o: 1.16, h: 1.18, l: 1.15, c: 1.162 },
      { t: "not-a-date", o: 1, h: 1, l: 1, c: 1 },
    ]);
    expect(candles).toHaveLength(2);
    expect(Number(candles[0].time)).toBeLessThan(Number(candles[1].time));
    expect(candles[1].close).toBe(1.162);
    expect(FX_HISTORY_DUPLICATES_DROPPED).toBeGreaterThan(0);
    expect(FX_INVALID_TIMESTAMPS_DROPPED).toBeGreaterThan(0);
    const times = candles.map((c) => Number(c.time));
    expect(times.every((t, i) => i === 0 || t > times[i - 1])).toBe(true);
    expect(lastSeriesTimestampOf(candles)).toBe(Number(candles[1].time));
    expect(normalizeHistoryCandles(candles as FxCandle[])).toEqual(candles);
  });

  it("safe updater appends, updates same ts, and drops older bars without throwing", () => {
    const update = vi.fn();
    const first = { time: T_1M_LAST as FxCandle["time"], open: 1.16, high: 1.16, low: 1.16, close: 1.16 };
    const same = { ...first, close: 1.161 };
    const older = { ...first, time: (T_1M_LAST - 60) as FxCandle["time"], close: 1.15 };
    expect(safeUpdateCandlestick({ update }, first, 0).result).toBe("appended");
    expect(safeUpdateCandlestick({ update }, same, T_1M_LAST).result).toBe("updated");
    const dropped = safeUpdateCandlestick({ update }, older, T_1M_LAST);
    expect(dropped.result).toBe("dropped_stale");
    expect(dropped.lastSeriesTimestamp).toBe(T_1M_LAST);
    expect(STALE_LIVE_UPDATES_DROPPED).toBe(1);
    expect(update).toHaveBeenCalledTimes(2);
    const exploding = {
      update: () => {
        throw new Error("Cannot update oldest data, last time=[object Object], new time=[object Object]");
      },
    };
    expect(safeUpdateCandlestick(exploding, first, 0).result).toBe("dropped_error");
    expect(STALE_LIVE_UPDATES_DROPPED).toBe(2);
  });

  it("resets the live bucket for the new timeframe instead of keeping the old bar time", () => {
    expect(candleBucketUnix("1m", T_QUOTE)).toBe(T_1M_LAST);
    expect(candleBucketUnix("5m", T_QUOTE)).toBe(T_5M_BUCKET);
    expect(T_5M_BUCKET).toBeLessThan(T_1M_LAST);
    const seeded = applyQuoteToActiveCandle(null, 1.1612, T_QUOTE, "5m");
    expect(Number(seeded?.time)).toBe(T_5M_BUCKET);
    expect(Number(seeded?.time)).not.toBe(T_1M_LAST);
  });

  async function switchTf(
    rerender: (ui: ReactElement) => void,
    Chart: typeof EurUsdNativeChart | typeof DxyNativeChart,
    tf: string,
    mid: string,
  ) {
    rerender(<Chart timeframe={tf} liveQuote={quote(mid)} />);
    await waitFor(() => expect(screen.getByTestId(Chart === DxyNativeChart ? "dxy-native-chart" : "eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
  }

  it("survives EURUSD 1m -> 5m while a live quote is in flight", async () => {
    const { rerender } = render(<EurUsdNativeChart timeframe="1m" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-live-follow")).toBe("yes");
    const gen1 = screen.getByTestId("eurusd-native-chart").getAttribute("data-chart-generation");
    await switchTf(rerender, EurUsdNativeChart, "5m", "1.16110");
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready");
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-live-follow")).toBe("yes");
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-chart-generation")).not.toBe(gen1);
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-visible-range-bars")).toBe("100");
    const lastUpdate = series.update.mock.calls.at(-1)?.[0] as FxCandle | undefined;
    if (lastUpdate) expect(Number(lastUpdate.time)).toBeGreaterThanOrEqual(T_5M_BUCKET);
  });

  it("survives EURUSD 5m -> 1m", async () => {
    const { rerender } = render(<EurUsdNativeChart timeframe="5m" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    await switchTf(rerender, EurUsdNativeChart, "1m", "1.16120");
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready");
  });

  it("walks EURUSD through every timeframe and back to 1m", async () => {
    const { rerender } = render(<EurUsdNativeChart timeframe="1m" liveQuote={quote("1.16100")} />);
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    for (const tf of ["5m", "15m", "1h", "4h", "1D", "1W", "1m"] as const) {
      await switchTf(rerender, EurUsdNativeChart, tf, "1.16100");
      expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready");
    }
  });

  it("ignores a late 1m history callback after switching to 5m", async () => {
    const pending: Record<string, (value: unknown) => void> = {};
    vi.mocked(cryptoFxIntelGet).mockImplementation((path: string) => {
      const u = decodeURIComponent(String(path));
      const key = u.includes("timeframe=5m") ? "5m" : u.includes("timeframe=1m") ? "1m" : "other";
      return new Promise((resolve) => {
        pending[key] = resolve;
      });
    });
    const { rerender } = render(<EurUsdNativeChart timeframe="1m" liveQuote={quote("1.16100")} />);
    rerender(<EurUsdNativeChart timeframe="5m" liveQuote={quote("1.16100")} />);
    expect(pending["1m"]).toBeTypeOf("function");
    expect(pending["5m"]).toBeTypeOf("function");
    series.setData.mockClear();
    await act(async () => {
      pending["1m"]?.(eurusd1m);
      await Promise.resolve();
    });
    const afterLate1m = series.setData.mock.calls.map((c) => (c[0] as FxCandle[]).length);
    await act(async () => {
      pending["5m"]?.(eurusd5m);
      await Promise.resolve();
    });
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    const lastNonEmpty = [...series.setData.mock.calls].reverse().find((c) => (c[0] as FxCandle[]).length > 0)?.[0] as FxCandle[];
    expect(lastNonEmpty.length).toBe(eurusd5m.json.bars.length);
    expect(afterLate1m.every((n) => n === 0)).toBe(true);
  });

  it("rapid EURUSD 1m -> 5m -> 1m -> 5m -> 15m -> 1m without waiting", async () => {
    const { rerender } = render(<EurUsdNativeChart timeframe="1m" liveQuote={quote("1.16100")} />);
    for (const tf of ["5m", "1m", "5m", "15m", "1m"] as const) {
      rerender(<EurUsdNativeChart timeframe={tf} liveQuote={quote("1.16100")} />);
    }
    await waitFor(() => expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-visible-range-bars")).toBe("100");
  });

  it("survives DXY 1m -> 5m with coarser Yahoo fallback bars", async () => {
    const { rerender } = render(<DxyNativeChart timeframe="1m" liveQuote={quote("99.274")} />);
    await waitFor(() => expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("ready"));
    await switchTf(rerender, DxyNativeChart, "5m", "99.276");
    expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("ready");
    rerender(<DxyNativeChart timeframe="1m" liveQuote={quote("99.277")} />);
    await waitFor(() => expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("ready"));
  });

  it("ignores a late DXY 1m callback after 5m and stays mounted", async () => {
    const pending: Record<string, (value: unknown) => void> = {};
    vi.mocked(cryptoFxIntelGet).mockImplementation((path: string) => {
      const u = decodeURIComponent(String(path));
      const key = u.includes("timeframe=5m") ? "5m" : "1m";
      return new Promise((resolve) => {
        pending[key] = resolve;
      });
    });
    const { rerender } = render(<DxyNativeChart timeframe="1m" liveQuote={quote("99.270")} />);
    rerender(<DxyNativeChart timeframe="5m" liveQuote={quote("99.270")} />);
    await act(async () => {
      pending["1m"]?.(dxyHourly);
      await Promise.resolve();
    });
    await act(async () => {
      pending["5m"]?.(dxyHourly);
      await Promise.resolve();
    });
    await waitFor(() => expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("ready"));
    expect(screen.getByTestId("dxy-native-chart")).toBeTruthy();
  });

  it("rapid DXY switches do not throw chronological update errors", async () => {
    const { rerender } = render(<DxyNativeChart timeframe="1m" liveQuote={quote("99.270")} />);
    for (const tf of ["5m", "1m", "5m", "15m", "1m"] as const) {
      rerender(<DxyNativeChart timeframe={tf} liveQuote={quote("99.271")} />);
    }
    await waitFor(() => expect(screen.getByTestId("dxy-native-chart").getAttribute("data-status")).toBe("ready"));
  });
});
