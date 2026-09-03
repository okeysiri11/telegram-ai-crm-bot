/**
 * Native EUR/USD candlesticks via Lightweight Charts.
 * Data: backend /fx-intel/candles (Yahoo EURUSD=X). TradingView is not used.
 */
import { useEffect, useRef, useState } from "react";
import { createChart, type IChartApi, type ISeriesApi } from "lightweight-charts";
import { Button } from "@/ui";
import type { ChartTimeframe } from "./chartProvider";
import { formatFxQuote } from "./fxQuoteDisplay";
import { barsToCandles, fetchFxCandles, type NativeCandleBar } from "./fxNativeChartCore";

export function EurUsdNativeChart({
  symbol = "EUR/USD",
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
  const [reload, setReload] = useState(0);
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
          setMessage("Не удалось загрузить график EURUSD");
          seriesRef.current?.setData([]);
          return;
        }
        const bars = Array.isArray(json.bars) ? (json.bars as NativeCandleBar[]) : [];
        const candles = barsToCandles(bars);
        seriesRef.current?.setData(candles);
        chartRef.current?.timeScale().fitContent();
        setMeta({
          barCount: Number(json.bar_count ?? candles.length) || candles.length,
          source: String(json.source || json.provider || "Yahoo Finance (EURUSD=X)"),
          lastClose: json.last_close ?? candles.at(-1)?.close,
        });
        if (!candles.length) {
          setStatus("error");
          setMessage("Не удалось загрузить график EURUSD");
          return;
        }
        setStatus("ready");
        setMessage(`Баров: ${candles.length}`);
      } catch {
        if (cancelled) return;
        setStatus("error");
        setMessage("Не удалось загрузить график EURUSD");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol, timeframe, reload]);

  return (
    <div
      className="w-full"
      data-testid="eurusd-native-chart"
      data-symbol={symbol}
      data-engine="lightweight-charts"
      data-status={status}
      data-bar-count={String(meta.barCount)}
      data-last-close={formatFxQuote(meta.lastClose, 5) ?? ""}
    >
      <div
        ref={hostRef}
        className="w-full overflow-hidden rounded-md border border-[var(--eds-border)] bg-white"
        style={{ height }}
        data-testid="eurusd-chart-canvas"
      />
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 eds-type-caption text-[var(--eds-text-muted)]">
        <span data-testid="eurusd-chart-status">
          {status === "loading" ? "Загрузка…" : status === "ready" ? "ADOS · Lightweight Charts" : "Ошибка"}
        </span>
        <span data-testid="eurusd-chart-bars">{message}</span>
        {meta.source ? <span>{meta.source}</span> : null}
        {formatFxQuote(liveQuote?.mid, 4) ? (
          <span data-testid="eurusd-live-quote">
            Live: {formatFxQuote(liveQuote?.mid, 4)}
            {liveQuote?.source ? ` · ${String(liveQuote.source)}` : ""}
          </span>
        ) : null}
        {status === "error" ? (
          <Button size="sm" variant="secondary" data-testid="eurusd-chart-retry" onClick={() => setReload((n) => n + 1)}>
            Повторить
          </Button>
        ) : null}
      </div>
      <p className="eds-type-caption text-[var(--eds-text-muted)]">
        EUR/USD: нативный график по барам бэкенда (Yahoo EURUSD=X). TradingView не используется.
      </p>
    </div>
  );
}
