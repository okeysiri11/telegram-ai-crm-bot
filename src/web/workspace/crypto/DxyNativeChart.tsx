/**
 * Sprint 50.7 — native DXY (and optional FX) candle chart via Lightweight Charts.
 * Data: backend /fx-intel/candles (Yahoo DX-Y.NYB). Never embeds TradingView for DXY.
 */
import { useEffect, useRef, useState } from "react";
import { createChart, type IChartApi, type ISeriesApi, type CandlestickData, type UTCTimestamp } from "lightweight-charts";
import { cryptoFxIntelGet } from "../business-ops/opsApi";
import type { ChartTimeframe } from "./chartProvider";

export const DXY_NATIVE_TIMEFRAMES: ChartTimeframe[] = ["15m", "1h", "4h", "1D"];

export type NativeCandleBar = {
  t: string;
  o: number;
  h: number;
  l: number;
  c: number;
  v?: number | null;
};

function toUtcTs(iso: string): UTCTimestamp {
  const ms = Date.parse(iso);
  return Math.floor((Number.isFinite(ms) ? ms : Date.now()) / 1000) as UTCTimestamp;
}

export function barsToCandles(bars: NativeCandleBar[]): CandlestickData[] {
  const out: CandlestickData[] = [];
  let prev = 0;
  for (const b of bars) {
    let t = toUtcTs(b.t);
    // lightweight-charts requires strictly ascending unique times
    if (t <= prev) t = (prev + 1) as UTCTimestamp;
    prev = t;
    out.push({
      time: t,
      open: Number(b.o),
      high: Number(b.h),
      low: Number(b.l),
      close: Number(b.c),
    });
  }
  return out;
}

export function normalizeCandlesTimeframe(tf: string): string {
  const u = tf.trim();
  const map: Record<string, string> = {
    "15m": "15m",
    "15M": "15m",
    "1h": "1H",
    "1H": "1H",
    "4h": "4H",
    "4H": "4H",
    "1d": "1D",
    "1D": "1D",
  };
  return map[u] || "1H";
}

export async function fetchFxCandles(symbol: string, timeframe: string) {
  const tf = normalizeCandlesTimeframe(timeframe);
  const res = await cryptoFxIntelGet(`/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(tf)}`);
  return { ok: res.ok, json: (res.json || {}) as Record<string, unknown> };
}

export function DxyNativeChart({
  symbol = "DXY",
  timeframe,
  height = 360,
  liveQuote,
}: {
  symbol?: string;
  timeframe: ChartTimeframe | string;
  height?: number;
  liveQuote?: { mid?: unknown; source?: string; fetched_at?: string; status?: string } | null;
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState<string>("Загрузка баров…");
  const [meta, setMeta] = useState<{ barCount: number; source?: string; lastClose?: unknown }>({ barCount: 0 });

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
    };
  }, [height]);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    setMessage("Загрузка баров…");
    void (async () => {
      try {
        const { ok, json } = await fetchFxCandles(symbol, String(timeframe));
        if (cancelled) return;
        if (!ok || json.status === "error" || json.chart_ready === false) {
          setStatus("error");
          setMessage(String(json.message || "Не удалось загрузить бары DXY"));
          seriesRef.current?.setData([]);
          return;
        }
        const bars = Array.isArray(json.bars) ? (json.bars as NativeCandleBar[]) : [];
        const candles = barsToCandles(bars);
        seriesRef.current?.setData(candles);
        chartRef.current?.timeScale().fitContent();
        setMeta({
          barCount: Number(json.bar_count ?? candles.length) || candles.length,
          source: String(json.source || json.provider || ""),
          lastClose: json.last_close ?? candles.at(-1)?.close,
        });
        if (!candles.length) {
          setStatus("error");
          setMessage("Нет баров для отображения");
          return;
        }
        setStatus("ready");
        setMessage(`Баров: ${candles.length}`);
      } catch (exc) {
        if (cancelled) return;
        setStatus("error");
        setMessage(exc instanceof Error ? exc.message : "Ошибка загрузки графика");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol, timeframe]);

  return (
    <div className="w-full" data-testid="dxy-native-chart" data-symbol={symbol} data-engine="lightweight-charts">
      <div
        ref={hostRef}
        className="w-full overflow-hidden rounded-md border border-[var(--eds-border)] bg-white"
        style={{ height }}
        data-testid="dxy-chart-canvas"
      />
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 eds-type-caption text-[var(--eds-text-muted)]">
        <span data-testid="dxy-chart-status">
          {status === "loading" ? "Загрузка…" : status === "ready" ? "ADOS · Lightweight Charts" : "Ошибка"}
        </span>
        <span data-testid="dxy-chart-bars">{message}</span>
        {meta.source ? <span>{meta.source}</span> : null}
        {liveQuote?.mid != null ? (
          <span data-testid="dxy-live-quote">
            Live: {String(liveQuote.mid)}
            {liveQuote.source ? ` · ${String(liveQuote.source)}` : ""}
          </span>
        ) : null}
        {status === "error" ? <span className="text-[var(--eds-danger,#b91c1c)]">{message}</span> : null}
      </div>
      <p className="eds-type-caption text-[var(--eds-text-muted)]">
        DXY: нативный график по барам бэкенда (Yahoo DX-Y.NYB). TradingView TVC:DXY не используется — без popup/логина.
      </p>
    </div>
  );
}
