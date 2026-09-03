/**
 * Shared live FX native chart: historical candles + quote overlay via series.update().
 * Does not refetch full history on every quote tick.
 */
import { useEffect, useRef, useState } from "react";
import { createChart, type IChartApi, type ISeriesApi } from "lightweight-charts";
import type { ChartTimeframe } from "./chartProvider";
import {
  applyQuoteToActiveCandle,
  barsToCandles,
  fetchFxCandles,
  formatLiveUpdated,
  fxHistoryRefreshMs,
  liveQuoteIsStale,
  parseQuoteMid,
  quoteTimeUnix,
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
  const liveQuoteRef = useRef(liveQuote);
  liveQuoteRef.current = liveQuote;

  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState<string>("Загрузка баров…");
  const [meta, setMeta] = useState<FxNativeLiveMeta>({ barCount: 0 });
  const [nowMs, setNowMs] = useState(() => Date.now());
  const [lastQuoteMs, setLastQuoteMs] = useState<number | null>(() => {
    const ms = Date.parse(String(liveQuote?.fetched_at || ""));
    return Number.isFinite(ms) ? ms : null;
  });

  const applyLive = (quote: LiveFxQuote | null | undefined) => {
    const series = seriesRef.current;
    const last = lastCandleRef.current;
    if (!series || !last) return;
    const mid = parseQuoteMid(quote?.mid);
    if (mid == null) return;
    const next = applyQuoteToActiveCandle(last, mid, quoteTimeUnix(quote), String(timeframe));
    if (!next) return;
    lastCandleRef.current = next;
    series.update(next);
    setMeta((prev) => ({ ...prev, lastClose: next.close }));
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
      rightPriceScale: { borderColor: "#cbd5e1" },
      timeScale: { borderColor: "#cbd5e1", timeVisible: true, secondsVisible: false },
      crosshair: { mode: 1 },
    });
    const series = chart.addCandlestickSeries({
      upColor: "#15803d",
      downColor: "#b91c1c",
      borderVisible: false,
      wickUpColor: "#15803d",
      wickDownColor: "#b91c1c",
      lastValueVisible: true,
      priceLineVisible: true,
      priceFormat: { type: "price", precision: pricePrecision, minMove },
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const ro = new ResizeObserver(() => {
      if (!hostRef.current || !chartRef.current) return;
      chartRef.current.applyOptions({ width: hostRef.current.clientWidth, height });
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      lastCandleRef.current = null;
    };
  }, [height, minMove, pricePrecision]);

  useEffect(() => {
    const ac = new AbortController();
    let inFlight = false;
    lastCandleRef.current = null;

    const loadHistory = async (silent: boolean) => {
      if (ac.signal.aborted || inFlight) return;
      inFlight = true;
      if (!silent) {
        setStatus("loading");
        setMessage("Загрузка баров…");
      }
      try {
        const { ok, json, cancelled } = await fetchFxCandles(symbol, String(timeframe), ac.signal);
        if (cancelled || ac.signal.aborted) return;
        if (!ok || json.status === "error" || json.chart_ready === false) {
          if (!silent) {
            setStatus("error");
            setMessage(useApiErrorMessage && json.message ? String(json.message) : loadError);
            seriesRef.current?.setData([]);
            lastCandleRef.current = null;
          }
          return;
        }
        const bars = Array.isArray(json.bars) ? (json.bars as NativeCandleBar[]) : [];
        const candles = barsToCandles(bars);
        seriesRef.current?.setData(candles);
        lastCandleRef.current = candles.at(-1) ?? null;
        if (!silent) {
          chartRef.current?.timeScale().fitContent();
        }
        setMeta({
          barCount: Number(json.bar_count ?? candles.length) || candles.length,
          source: String(json.source || json.provider || ""),
          lastClose: json.last_close ?? candles.at(-1)?.close,
        });
        if (!candles.length) {
          if (!silent) {
            setStatus("error");
            setMessage(emptyError);
          }
          return;
        }
        setStatus("ready");
        setMessage(`Баров: ${candles.length}`);
        applyLive(liveQuoteRef.current);
      } catch {
        if (ac.signal.aborted) return;
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
      ac.abort();
      if (historyId) window.clearInterval(historyId);
    };
  }, [symbol, timeframe, reload, loadError, emptyError, useApiErrorMessage]);

  useEffect(() => {
    applyLive(liveQuote);
    const mid = parseQuoteMid(liveQuote?.mid);
    if (mid == null) return;
    const ms = Date.parse(String(liveQuote?.fetched_at || ""));
    setLastQuoteMs(Number.isFinite(ms) ? ms : Date.now());
  }, [liveQuote, timeframe]);

  useEffect(() => {
    const id = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const fetchedAt = liveQuote?.fetched_at;
  const updated = formatLiveUpdated(fetchedAt);
  const hasQuote = parseQuoteMid(liveQuote?.mid) != null && lastQuoteMs != null;
  const stale = !hasQuote || liveQuoteIsStale(lastQuoteMs, nowMs);

  return {
    hostRef,
    status,
    message,
    meta,
    liveKind: (stale ? "STALE" : "LIVE") as "LIVE" | "STALE",
    liveUpdated: updated,
    lastQuoteMs,
  };
}

export function FxLiveStatusCaption({
  testIdPrefix,
  liveKind,
  liveUpdated,
}: {
  testIdPrefix: string;
  liveKind: "LIVE" | "STALE";
  liveUpdated: string | null;
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
    </span>
  );
}
