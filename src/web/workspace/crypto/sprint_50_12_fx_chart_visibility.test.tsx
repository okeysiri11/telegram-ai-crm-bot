/**
 * Sprint 50.12 — recent viewport, autoscale margins, live-follow (no OHLC distortion).
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { createChart } from "lightweight-charts";
import { EurUsdNativeChart } from "./EurUsdNativeChart";
import {
  applyQuoteToActiveCandle,
  FX_PRICE_SCALE_MARGIN_BOTTOM,
  FX_PRICE_SCALE_MARGIN_TOP,
  fxInitialLogicalRange,
  fxVisibleBarCount,
  userLeftLiveFollow,
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

function manyBars(n: number) {
  const bars = [];
  const start = Date.parse("2026-09-03T00:00:00Z");
  for (let i = 0; i < n; i += 1) {
    const t = new Date(start + i * 60_000).toISOString();
    const c = 1.16 + (i % 5) * 0.0001;
    bars.push({ t, o: c, h: c + 0.0002, l: c - 0.0002, c });
  }
  return bars;
}

const history150 = {
  ok: true,
  json: {
    status: "connected",
    chart_ready: true,
    bar_count: 150,
    source: "Yahoo Finance (EURUSD=X)",
    last_close: 1.1604,
    bars: manyBars(150),
  },
};

describe("sprint 50.12 chart visibility", () => {
  beforeEach(() => {
    // @ts-expect-error test stub
    global.ResizeObserver = class {
      observe() {}
      disconnect() {}
      unobserve() {}
    };
    series.setData.mockClear();
    series.update.mockClear();
    timeScale.fitContent.mockClear();
    timeScale.setVisibleLogicalRange.mockClear();
    timeScale.subscribeVisibleLogicalRangeChange.mockClear();
    vi.mocked(cryptoFxIntelGet).mockResolvedValue(history150);
    vi.mocked(createChart).mockClear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

    it("maps initial visible logical range per timeframe", () => {
    expect(fxVisibleBarCount("1m")).toBe(100);
    expect(fxVisibleBarCount("5m")).toBe(100);
    expect(fxVisibleBarCount("15m")).toBe(100);
    expect(fxVisibleBarCount("1h")).toBe(90);
    expect(fxVisibleBarCount("4h")).toBe(80);
    expect(fxVisibleBarCount("1D")).toBe(90);
    expect(fxVisibleBarCount("1W")).toBe(70);
    expect(fxInitialLogicalRange(500, 100)).toEqual({ from: 400, to: 503 });
    expect(fxInitialLogicalRange(80, 100).from).toBe(0);
    expect(FX_PRICE_SCALE_MARGIN_TOP).toBe(0.12);
    expect(FX_PRICE_SCALE_MARGIN_BOTTOM).toBe(0.12);
  });

  it("detects when the user pans away from the latest candle", () => {
    expect(userLeftLiveFollow({ from: 380, to: 503 }, 499)).toBe(false);
    expect(userLeftLiveFollow({ from: 0, to: 40 }, 499)).toBe(true);
  });

  it("does not invent OHLC beyond the real quote", () => {
    const last: FxCandle = { time: 1_000 as FxCandle["time"], open: 1.16, high: 1.161, low: 1.159, close: 1.16 };
    const same = applyQuoteToActiveCandle(last, 1.16, 1_010, "1m");
    expect(same?.open).toBe(1.16);
    expect(same?.close).toBe(1.16);
    expect(same?.high).toBe(1.161);
    expect(same?.low).toBe(1.159);
  });

  it("sets recent logical range and autoscale margins on first load, not fitContent", async () => {
    render(
      <EurUsdNativeChart timeframe="1m" liveQuote={{ mid: "1.16040", fetched_at: new Date().toISOString(), status: "live" }} />,
    );
    await waitFor(() => expect(series.setData).toHaveBeenCalled());
    expect(timeScale.fitContent).not.toHaveBeenCalled();
    expect(timeScale.setVisibleLogicalRange).toHaveBeenCalled();
    const range = timeScale.setVisibleLogicalRange.mock.calls.at(-1)?.[0] as { from: number; to: number };
    expect(range.to - range.from).toBe(103);
    expect(range.from).toBeGreaterThanOrEqual(30);
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-visible-range-bars")).toBe("100");
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-live-follow")).toBe("yes");
    const opts = vi.mocked(createChart).mock.calls[0]?.[1] as {
      rightPriceScale?: { scaleMargins?: { top: number; bottom: number }; autoScale?: boolean };
    };
    expect(opts.rightPriceScale?.autoScale).toBe(true);
    expect(opts.rightPriceScale?.scaleMargins).toEqual({ top: 0.12, bottom: 0.12 });
  });

  it("does not reset the viewport on a same-bucket live quote", async () => {
    const lastIso = history150.json.bars.at(-1)?.t as string;
    const { rerender } = render(
      <EurUsdNativeChart timeframe="1m" liveQuote={{ mid: "1.16040", fetched_at: lastIso, status: "live" }} />,
    );
    await waitFor(() => expect(series.setData).toHaveBeenCalled());
    const afterLoad = timeScale.setVisibleLogicalRange.mock.calls.length;
    expect(timeScale.fitContent).not.toHaveBeenCalled();
    rerender(
      <EurUsdNativeChart
        timeframe="1m"
        liveQuote={{ mid: "1.16050", fetched_at: new Date(Date.parse(lastIso) + 20_000).toISOString(), status: "live" }}
      />,
    );
    await waitFor(() => expect(series.update).toHaveBeenCalled());
    expect(timeScale.setVisibleLogicalRange.mock.calls.length).toBe(afterLoad);
    expect(timeScale.fitContent).not.toHaveBeenCalled();
    const updated = series.update.mock.calls.at(-1)?.[0] as FxCandle;
    expect(updated.close).toBe(1.1605);
    expect(updated.open).not.toBeUndefined();
  });

  it("turns off live-follow on user pan and restores it from К текущей цене", async () => {
    render(
      <EurUsdNativeChart timeframe="1m" liveQuote={{ mid: "1.16040", fetched_at: new Date().toISOString(), status: "live" }} />,
    );
    await waitFor(() => expect(timeScale.subscribeVisibleLogicalRangeChange).toHaveBeenCalled());
    expect(screen.queryByTestId("eurusd-follow-live")).toBeNull();
    const onRange = timeScale.subscribeVisibleLogicalRangeChange.mock.calls[0][0] as (r: { from: number; to: number }) => void;
    act(() => {
      onRange({ from: 0, to: 20 });
    });
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-live-follow")).toBe("no");
    const afterPan = timeScale.setVisibleLogicalRange.mock.calls.length;
    expect(await screen.findByTestId("eurusd-follow-live")).toBeTruthy();
    fireEvent.click(screen.getByTestId("eurusd-follow-live"));
    expect(screen.getByTestId("eurusd-native-chart").getAttribute("data-live-follow")).toBe("yes");
    expect(timeScale.setVisibleLogicalRange.mock.calls.length).toBeGreaterThan(afterPan);
    expect(timeScale.fitContent).not.toHaveBeenCalled();
  });
});
