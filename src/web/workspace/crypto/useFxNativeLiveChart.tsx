/**
 * Shared live FX native chart: historical candles + quote overlay via series.update().
 * Does not refetch full history on every quote tick.
 * Viewport: recent logical window + live-follow; never fitContent on quote ticks.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { createChart, type IChartApi, type ISeriesApi, type LogicalRange } from "lightweight-charts";
import { Button } from "@/ui";
import type { ChartTimeframe } from "./chartProvider";
import {
  applyQuoteToActiveCandle,
  barsToCandles,
  fetchFxCandles,
  formatLiveUpdated,
  fxHistoryRefreshMs,
  fxInitialLogicalRange,
  fxVisibleBarCount,
  FX_PRICE_SCALE_MARGIN_BOTTOM,
  FX_PRICE_SCALE_MARGIN_TOP,
  lastSeriesTimestampOf,
  liveQuoteIsStale,
  parseQuoteMid,
  quoteTimeUnix,
  safeUpdateCandlestick,
  STALE_LIVE_UPDATES_DROPPED,
  userLeftLiveFollow,
  type FxCandle,
  type LiveFxQuote,
  type NativeCandleBar,
} from "./fxNativeChartCore";

export type FxNativeLiveMeta = { barCount: number; source?: string; lastClose?: unknown };

export function useFxNativeLiveChart({
  symbol,
  timeframe,
  height,
  liveQuote,
  pricePrecision,
  minMove,
  loadError,
  emptyError,
  reload = 0,
  useApiErrorMessage = false,
}: {
  symbol: string;
  timeframe: ChartTimeframe | string;
  height: number;
  liveQuote?: LiveFxQuote | null;
  pricePrecision: number;
  minMove: number;
  loadError: string;
  emptyError: string;
  reload?: number;
  useApiErrorMessage?: boolean;
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const lastCandleRef = useRef<FxCandle | null>(null);
  const lastSeriesTimestampRef = useRef(0);
  const liveQuoteRef = useRef(liveQuote);
  const timeframeRef = useRef(timeframe);
  const followRef = useRef(true);
  const applyingRangeRef = useRef(false);
  const lastIndexRef = useRef(0);
  const historyReadyRef = useRef(false);
  const liveEnabledRef = useRef(false);
  const generationRef = useRef(0);
  liveQuoteRef.current = liveQuote;
  timeframeRef.current = timeframe;

  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState<string>("Загрузка баров…");
  const [meta, setMeta] = useState<FxNativeLiveMeta>({ barCount: 0 });
  const [nowMs, setNowMs] = useState(() => Date.now());
  const [followLive, setFollowLive] = useState(true);
  const [staleDropped, setStaleDropped] = useState(0);
  const [generation, setGeneration] = useState(0);
  const [lastQuoteMs, setLastQuoteMs] = useState<number | null>(() => {
    const ms = Date.parse(String(liveQuote?.fetched_at || ""));
    return Number.isFinite(ms) ? ms : null;
  });

  const applyRecentViewport = useCallback((barCount: number) => {
    const chart = chartRef.current;
    if (!chart || barCount <= 0) return;
    const range = fxInitialLogicalRange(barCount, fxVisibleBarCount(String(timeframeRef.current)));
    applyingRangeRef.current = true;
    chart.timeScale().setVisibleLogicalRange(range);
    applyingRangeRef.current = false;
  }, []);

  const goToLive = useCallback(() => {
    followRef.current = true;
    setFollowLive(true);
    applyRecentViewport(lastIndexRef.current + 1);
  }, [applyRecentViewport]);

  const applyLive = (quote: LiveFxQuote | null | undefined, requestGeneration?: number) => {
    if (requestGeneration != null && requestGeneration !== generationRef.current) return;
    if (!liveEnabledRef.current) return;
    const series = seriesRef.current;
    if (!series) return;
    const mid = parseQuoteMid(quote?.mid);
    if (mid == null) return;
    const prev = lastCandleRef.current;
    const next = applyQuoteToActiveCandle(prev, mid, quoteTimeUnix(quote), String(timeframeRef.current));
    if (!next) return;
    const safe = safeUpdateCandlestick(series, next, lastSeriesTimestampRef.current);
    if (safe.result === "dropped_stale" || safe.result === "dropped_invalid" || safe.result === "dropped_error") {
      setStaleDropped(STALE_LIVE_UPDATES_DROPPED);
      return;
    }
    const bar = safe.bar ?? next;
    const appended = safe.result === "appended";
    lastCandleRef.current = bar;
    lastSeriesTimestampRef.current = safe.lastSeriesTimestamp;
    setMeta((curr) => ({ ...curr, lastClose: bar.close }));
    if (appended) {
      lastIndexRef.current = prev ? lastIndexRef.current + 1 : Math.max(0, lastIndexRef.current);
      if (historyReadyRef.current && followRef.current) applyRecentViewport(lastIndexRef.current + 1);
    }
  };

  useEffect(() => {
    const el = hostRef.current;
    if (!el) return;

    const chart = createChart(el, {
      width: el.clientWidth || el.parentElement?.clientWidth || 640,
      height,
      layout: {
        background: { color: "#ffffff" },
        textColor: "#334155",
      },
      grid: {
        vertLines: { color: "#e2e8f0" },
        horzLines: { color: "#e2e8f0" },
      },
      rightPriceScale: {
        borderColor: "#cbd5e1",
        autoScale: true,
        scaleMargins: { top: FX_PRICE_SCALE_MARGIN_TOP, bottom: FX_PRICE_SCALE_MARGIN_BOTTOM },
      },
      timeScale: { borderColor: "#cbd5e1", timeVisible: true, secondsVisible: false },
      crosshair: {
        mode: 1,
        horzLine: { visible: true, labelVisible: true, color: "#0f766e", width: 1 },
        vertLine: { visible: true, labelVisible: true },
      },
    });
    const series = chart.addCandlestickSeries({
      upColor: "#15803d",
      downColor: "#b91c1c",
      borderVisible: false,
      wickUpColor: "#15803d",
      wickDownColor: "#b91c1c",
      lastValueVisible: true,
      priceLineVisible: true,
      priceLineWidth: 2,
      priceLineColor: "#0f766e",
      priceFormat: { type: "price", precision: pricePrecision, minMove },
    });
    series.priceScale().applyOptions({
      autoScale: true,
      scaleMargins: { top: FX_PRICE_SCALE_MARGIN_TOP, bottom: FX_PRICE_SCALE_MARGIN_BOTTOM },
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const onRange = (range: LogicalRange | null) => {
      if (applyingRangeRef.current) return;
      if (userLeftLiveFollow(range, lastIndexRef.current)) {
        followRef.current = false;
        setFollowLive(false);
      }
    };
    const ts = chart.timeScale();
    ts.subscribeVisibleLogicalRangeChange(onRange);

    const ro = new ResizeObserver(() => {
      if (!hostRef.current || !chartRef.current) return;
      chartRef.current.applyOptions({ width: hostRef.current.clientWidth, height });
    });
    ro.observe(el);

    return () => {
      if (typeof ts.unsubscribeVisibleLogicalRangeChange === "function") {
        ts.unsubscribeVisibleLogicalRangeChange(onRange);
      }
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      lastCandleRef.current = null;
      lastSeriesTimestampRef.current = 0;
      liveEnabledRef.current = false;
    };
  }, [height, minMove, pricePrecision]);

  useEffect(() => {
    const ac = new AbortController();
    let inFlight = false;
    generationRef.current += 1;
    const requestGeneration = generationRef.current;
    setGeneration(requestGeneration);
    liveEnabledRef.current = false;
    lastCandleRef.current = null;
    lastSeriesTimestampRef.current = 0;
    historyReadyRef.current = false;
    followRef.current = true;
    setFollowLive(true);
    try {
      seriesRef.current?.setData([]);
    } catch {
      /* isolation: a failed clear must not crash the desk */
    }

    const loadHistory = async (silent: boolean) => {
      if (requestGeneration !== generationRef.current) return;
      if (ac.signal.aborted || inFlight) return;
      inFlight = true;
      if (!silent) {
        setStatus("loading");
        setMessage("Загрузка баров…");
      }
      try {
        const { ok, json, cancelled } = await fetchFxCandles(symbol, String(timeframe), ac.signal);
        if (cancelled || ac.signal.aborted || requestGeneration !== generationRef.current) return;
        if (!ok || json.status === "error" || json.chart_ready === false) {
          if (!silent) {
            setStatus("error");
            setMessage(useApiErrorMessage && json.message ? String(json.message) : loadError);
            try {
              seriesRef.current?.setData([]);
            } catch {
              /* isolation */
            }
            lastCandleRef.current = null;
            lastSeriesTimestampRef.current = 0;
            liveEnabledRef.current = false;
          }
          return;
        }
        const bars = Array.isArray(json.bars) ? (json.bars as NativeCandleBar[]) : [];
        const candles = barsToCandles(bars);
        try {
          seriesRef.current?.setData(candles);
        } catch (err) {
          console.warn("[fx-chart] series.setData rejected", err);
          if (!silent) {
            setStatus("error");
            setMessage(loadError);
          }
          return;
        }
        lastCandleRef.current = candles.at(-1) ?? null;
        lastSeriesTimestampRef.current = lastSeriesTimestampOf(candles);
        lastIndexRef.current = Math.max(0, candles.length - 1);
        historyReadyRef.current = candles.length > 0;
        liveEnabledRef.current = true;
        if (!silent || followRef.current) {
          applyRecentViewport(Math.max(candles.length, 1));
        }
        setMeta({
          barCount: Number(json.bar_count ?? candles.length) || candles.length,
          source: String(json.source || json.provider || ""),
          lastClose: json.last_close ?? candles.at(-1)?.close,
        });
        if (!candles.length) {
          applyLive(liveQuoteRef.current, requestGeneration);
          if (lastCandleRef.current) {
            historyReadyRef.current = true;
            lastIndexRef.current = 0;
            if (!silent || followRef.current) applyRecentViewport(1);
            setStatus("ready");
            setMessage("Баров: live");
            return;
          }
          if (!silent) {
            setStatus("error");
            setMessage(emptyError);
            liveEnabledRef.current = false;
          }
          return;
        }
        setStatus("ready");
        setMessage(`Баров: ${candles.length}`);
        applyLive(liveQuoteRef.current, requestGeneration);
      } catch {
        if (ac.signal.aborted || requestGeneration !== generationRef.current) return;
        if (!silent) {
          setStatus("error");
          setMessage(loadError);
        }
      } finally {
        inFlight = false;
      }
    };

    void loadHistory(false);
    const refreshMs = fxHistoryRefreshMs(String(timeframe));
    const historyId = refreshMs ? window.setInterval(() => void loadHistory(true), refreshMs) : 0;
    return () => {
      generationRef.current += 1;
      liveEnabledRef.current = false;
      ac.abort();
      if (historyId) window.clearInterval(historyId);
    };
  }, [symbol, timeframe, reload, loadError, emptyError, useApiErrorMessage, applyRecentViewport]);

  useEffect(() => {
    applyLive(liveQuote, generationRef.current);
    const mid = parseQuoteMid(liveQuote?.mid);
    if (mid == null) return;
    const ms = Date.parse(String(liveQuote?.fetched_at || ""));
    setLastQuoteMs(Number.isFinite(ms) ? ms : Date.now());
  }, [liveQuote]);

  useEffect(() => {
    const id = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const fetchedAt = liveQuote?.fetched_at;
  const updated = formatLiveUpdated(fetchedAt);
  const hasQuote = parseQuoteMid(liveQuote?.mid) != null && lastQuoteMs != null;
  const stale = !hasQuote || liveQuoteIsStale(lastQuoteMs, nowMs);
  const visibleBarCount = fxVisibleBarCount(String(timeframe));

  return {
    hostRef,
    status,
    message,
    meta,
    liveKind: (stale ? "STALE" : "LIVE") as "LIVE" | "STALE",
    liveUpdated: updated,
    lastQuoteMs,
    followLive,
    goToLive,
    visibleBarCount,
    generation,
    staleDropped,
  };
}

export function FxLiveStatusCaption({
  testIdPrefix,
  liveKind,
  liveUpdated,
  followLive,
  onGoToLive,
}: {
  testIdPrefix: string;
  liveKind: "LIVE" | "STALE";
  liveUpdated: string | null;
  followLive: boolean;
  onGoToLive: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-2" data-testid={`${testIdPrefix}-live-indicator`} data-live-status={liveKind.toLowerCase()}>
      {liveKind === "LIVE" ? (
        <span>
          LIVE <span className="text-[var(--eds-success,#15803d)]">●</span>
        </span>
      ) : (
        <span>STALE</span>
      )}
      {liveUpdated ? <span data-testid={`${testIdPrefix}-live-updated`}>Updated: {liveUpdated}</span> : null}
      {!followLive ? (
        <Button size="sm" variant="secondary" data-testid={`${testIdPrefix}-follow-live`} onClick={onGoToLive}>
          К текущей цене
        </Button>
      ) : null}
    </span>
  );
}
