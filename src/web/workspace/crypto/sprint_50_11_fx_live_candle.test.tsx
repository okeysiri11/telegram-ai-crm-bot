/**
 * Sprint 50.11 — live quote overlay on the active FX candle (no full-history refetch per tick).
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { EurUsdNativeChart } from "./EurUsdNativeChart";
import { DxyNativeChart } from "./DxyNativeChart";
import { FX_QUOTE_POLL_MS } from "./fxNativeChartCore";
import { formatFxQuote } from "./fxQuoteDisplay";
import {
  applyQuoteToActiveCandle,
  candleBucketUnix,
  formatLiveUpdated,
  fxHistoryRefreshMs,
  liveQuoteIsStale,
  LIVE_QUOTE_STALE_MS,
  parseQuoteMid,
  quoteTimeUnix,
  type FxCandle,
} from "./fxNativeChartCore";
import { cryptoFxIntelGet } from "../business-ops/opsApi";

const { series } = vi.hoisted(() => ({
  series: { setData: vi.fn(), update: vi.fn() },
}));

vi.mock("../business-ops/opsApi", () => ({
  cryptoFxIntelGet: vi.fn(),
}));

vi.mock("lightweight-charts", () => {
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

const hourBars = {
  ok: true,
  json: {
    status: "connected",
    chart_ready: true,
    bar_count: 2,
    source: "Yahoo Finance (EURUSD=X)",
    last_close: 1.1615,
    bars: [
      { t: "2026-09-03T06:00:00+00:00", o: 1.16, h: 1.162, l: 1.158, c: 1.161 },
      { t: "2026-09-03T07:00:00+00:00", o: 1.161, h: 1.162, l: 1.16, c: 1.1615 },
    ],
  },
};

function lastHour(): FxCandle {
  return { time: Date.parse("2026-09-03T07:00:00Z") / 1000, open: 1.161, high: 1.162, low: 1.16, close: 1.1615 };
}

describe("sprint 50.11 live active candle", () => {
  beforeEach(() => {
    // @ts-expect-error test stub
    global.ResizeObserver = class {
      observe() {}
      disconnect() {}
      unobserve() {}
    };
    series.setData.mockClear();
    series.update.mockClear();
    vi.mocked(cryptoFxIntelGet).mockResolvedValue(hourBars);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("maps timeframe buckets", () => {
    const t = Date.parse("2026-09-03T07:14:37Z") / 1000;
    expect(candleBucketUnix("1m", t)).toBe(Date.parse("2026-09-03T07:14:00Z") / 1000);
    expect(candleBucketUnix("5m", t)).toBe(Date.parse("2026-09-03T07:10:00Z") / 1000);
    expect(candleBucketUnix("15m", t)).toBe(Date.parse("2026-09-03T07:00:00Z") / 1000);
    expect(candleBucketUnix("1h", t)).toBe(Date.parse("2026-09-03T07:00:00Z") / 1000);
    expect(candleBucketUnix("4h", t)).toBe(Date.parse("2026-09-03T04:00:00Z") / 1000);
    expect(candleBucketUnix("1D", t)).toBe(Date.parse("2026-09-03T00:00:00Z") / 1000);
    expect(candleBucketUnix("1W", t)).toBe(Date.parse("2026-08-31T00:00:00Z") / 1000);
  });

  it("updates close/high/low inside the same candle and keeps open", () => {
    const last = lastHour();
    const quoteUnix = Date.parse("2026-09-03T07:12:00Z") / 1000;
    const up = applyQuoteToActiveCandle(last, 1.163, quoteUnix, "1h");
    expect(up).toEqual({ time: last.time, open: 1.161, high: 1.163, low: 1.16, close: 1.163 });
    const down = applyQuoteToActiveCandle(up, 1.159, quoteUnix, "1h");
    expect(down?.low).toBe(1.159);
    expect(down?.high).toBe(1.163);
    expect(down?.open).toBe(1.161);
    expect(down?.close).toBe(1.159);
    expect(down?.time).toBe(last.time);
  });

  it("appends the next candle without duplicating timestamps", () => {
    const last = lastHour();
    const nextUnix = Date.parse("2026-09-03T08:03:00Z") / 1000;
    const created = applyQuoteToActiveCandle(last, 1.164, nextUnix, "1h");
    expect(Number(created?.time)).toBe(Date.parse("2026-09-03T08:00:00Z") / 1000);
    expect(created?.open).toBe(1.1615);
    expect(created?.close).toBe(1.164);
    expect(Number(created?.time)).toBeGreaterThan(Number(last.time));
    const times = [Number(last.time), Number(created?.time)];
    expect(new Set(times).size).toBe(2);
    expect(applyQuoteToActiveCandle(created, 1.16, Date.parse("2026-09-03T07:30:00Z") / 1000, "1h")).toBeNull();
  });

  it("paints a first live candle when history is empty", () => {
    const created = applyQuoteToActiveCandle(null, 99.255, Date.parse("2026-09-03T07:14:37Z") / 1000, "1m");
    expect(created?.open).toBe(99.255);
    expect(created?.close).toBe(99.255);
    expect(Number(created?.time)).toBe(Date.parse("2026-09-03T07:14:00Z") / 1000);
  });

  it("does not invent prices and ignores non-finite quotes", () => {
    expect(parseQuoteMid("1.16157")).toBe(1.16157);
    expect(parseQuoteMid("NaN")).toBeNull();
    expect(applyQuoteToActiveCandle(lastHour(), Number.NaN, 1_000_000, "1h")).toBeNull();
  });

  it("formats EURUSD to 5 decimals and DXY to 3", () => {
    expect(formatFxQuote(1.16157, 5)).toBe("1.16157");
    expect(formatFxQuote("99.278", 3)).toBe("99.278");
  });

  it("marks stale after the live timeout and keeps quote time from fetched_at", () => {
    const fetched = "2026-09-03T07:07:19.208Z";
    expect(quoteTimeUnix({ fetched_at: fetched, market_time: 1 })).toBe(Math.floor(Date.parse(fetched) / 1000));
    expect(formatLiveUpdated(fetched, "en-GB")).toMatch(/\d{2}:\d{2}:\d{2}/);
    expect(liveQuoteIsStale(Date.now() - (LIVE_QUOTE_STALE_MS + 1), Date.now())).toBe(true);
    expect(liveQuoteIsStale(Date.now() - 5_000, Date.now())).toBe(false);
  });

  it("refreshes history only on short timeframes", () => {
    expect(fxHistoryRefreshMs("1m")).toBe(60_000);
    expect(fxHistoryRefreshMs("5m")).toBe(60_000);
    expect(fxHistoryRefreshMs("15m")).toBe(60_000);
    expect(fxHistoryRefreshMs("1h")).toBe(0);
    expect(fxHistoryRefreshMs("1W")).toBe(0);
    expect(FX_QUOTE_POLL_MS).toBe(5_000);
  });

  it("applies a changed live quote with series.update after history load", async () => {
    const fetched = new Date().toISOString();
    const { rerender } = render(
      <EurUsdNativeChart
        timeframe="1h"
        liveQuote={{ mid: "1.16150", fetched_at: fetched, status: "live", source: "Yahoo Finance (EURUSD=X)" }}
      />,
    );
    await waitFor(() => expect(series.setData).toHaveBeenCalled());
    const historyCalls = vi.mocked(cryptoFxIntelGet).mock.calls.length;
    series.update.mockClear();
    rerender(
      <EurUsdNativeChart
        timeframe="1h"
        liveQuote={{ mid: "1.16180", fetched_at: new Date(Date.now() + 5_000).toISOString(), status: "live" }}
      />,
    );
    await waitFor(() => expect(series.update).toHaveBeenCalled());
    const updated = series.update.mock.calls.at(-1)?.[0] as FxCandle;
    expect(updated.close).toBe(1.1618);
    expect(vi.mocked(cryptoFxIntelGet).mock.calls.length).toBe(historyCalls);
    expect(screen.getByTestId("eurusd-live-quote").textContent).toContain("1.16180");
    expect(screen.getByTestId("eurusd-live-indicator").textContent).toContain("LIVE");
    expect(screen.getByTestId("eurusd-live-updated").textContent).toMatch(/Updated: \d{2}:\d{2}:\d{2}/);
  });

  it("shows STALE when the last quote is older than 30 seconds", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-09-03T07:07:10Z"));
    render(
      <EurUsdNativeChart
        timeframe="1h"
        liveQuote={{ mid: "1.16150", fetched_at: "2026-09-03T07:07:00Z", status: "live" }}
      />,
    );
    await act(async () => {
      await Promise.resolve();
    });
    expect(screen.getByTestId("eurusd-live-indicator").getAttribute("data-live-status")).toBe("live");
    await act(async () => {
      vi.advanceTimersByTime(31_000);
    });
    expect(screen.getByTestId("eurusd-live-indicator").getAttribute("data-live-status")).toBe("stale");
    expect(screen.getByTestId("eurusd-live-indicator").textContent).toContain("STALE");
  });

  it("clears history polling on unmount and timeframe switch", async () => {
    vi.useFakeTimers();
    const { rerender, unmount } = render(
      <EurUsdNativeChart timeframe="1m" liveQuote={{ mid: "1.16150", fetched_at: new Date().toISOString() }} />,
    );
    await act(async () => {
      await Promise.resolve();
    });
    const afterMount = vi.mocked(cryptoFxIntelGet).mock.calls.length;
    rerender(<EurUsdNativeChart timeframe="5m" liveQuote={{ mid: "1.16150", fetched_at: new Date().toISOString() }} />);
    await act(async () => {
      await Promise.resolve();
    });
    const afterTf = vi.mocked(cryptoFxIntelGet).mock.calls.length;
    expect(afterTf).toBeGreaterThan(afterMount);
    await act(async () => {
      vi.advanceTimersByTime(60_000);
    });
    const afterMinute = vi.mocked(cryptoFxIntelGet).mock.calls.length;
    unmount();
    await act(async () => {
      vi.advanceTimersByTime(120_000);
    });
    expect(vi.mocked(cryptoFxIntelGet).mock.calls.length).toBe(afterMinute);
  });

  it("updates DXY live close at 3 decimal display precision", async () => {
    vi.mocked(cryptoFxIntelGet).mockResolvedValue({
      ok: true,
      json: {
        status: "connected",
        chart_ready: true,
        bar_count: 1,
        source: "Yahoo Finance (DX-Y.NYB)",
        last_close: 99.27,
        bars: [{ t: "2026-09-03T07:00:00+00:00", o: 99.27, h: 99.28, l: 99.26, c: 99.27 }],
      },
    });
    const { rerender } = render(
      <DxyNativeChart timeframe="1h" liveQuote={{ mid: "99.270", fetched_at: new Date().toISOString(), status: "connected" }} />,
    );
    await waitFor(() => expect(series.setData).toHaveBeenCalled());
    rerender(
      <DxyNativeChart timeframe="1h" liveQuote={{ mid: "99.278", fetched_at: new Date().toISOString(), status: "connected" }} />,
    );
    await waitFor(() => expect(series.update).toHaveBeenCalled());
    expect(screen.getByTestId("dxy-live-quote").textContent).toContain("99.278");
    expect(screen.getByTestId("dxy-live-indicator").textContent).toContain("LIVE");
    expect(screen.getByTestId("dxy-native-chart").getAttribute("data-last-close")).toBe("99.278");
  });

  it("seeds an active candle from the quote when history bars are empty", async () => {
    vi.mocked(cryptoFxIntelGet).mockResolvedValue({
      ok: true,
      json: { status: "connected", chart_ready: true, bar_count: 0, bars: [], source: "Yahoo Finance (DX-Y.NYB)" },
    });
    const { rerender } = render(
      <DxyNativeChart timeframe="1m" liveQuote={{ mid: "99.255", fetched_at: new Date().toISOString(), status: "connected" }} />,
    );
    await waitFor(() => expect(series.update).toHaveBeenCalled());
    expect(series.update.mock.calls.at(-1)?.[0].close).toBe(99.255);
    rerender(
      <DxyNativeChart timeframe="1m" liveQuote={{ mid: "99.252", fetched_at: new Date().toISOString(), status: "connected" }} />,
    );
    await waitFor(() => expect(series.update.mock.calls.at(-1)?.[0].close).toBe(99.252));
    expect(screen.getByTestId("dxy-native-chart").getAttribute("data-last-close")).toBe("99.252");
  });
});
