/**
 * Sprint 50.7 — native DXY (and optional FX) candle chart via Lightweight Charts.
 * Data: backend /fx-intel/candles (Yahoo DX-Y.NYB) + live quote overlay. Never embeds TradingView for DXY.
 */
import type { ChartTimeframe } from "./chartProvider";
import { formatFxQuote } from "./fxQuoteDisplay";
import type { LiveFxQuote } from "./fxNativeChartCore";
import { FxLiveStatusCaption, useFxNativeLiveChart } from "./useFxNativeLiveChart";

export const DXY_NATIVE_TIMEFRAMES: ChartTimeframe[] = ["15m", "1h", "4h", "1D"];
export { barsToCandles, fetchFxCandles, normalizeCandlesTimeframe } from "./fxNativeChartCore";
export type { NativeCandleBar } from "./fxNativeChartCore";

export function DxyNativeChart({
  symbol = "DXY",
  timeframe,
  height = 360,
  liveQuote,
}: {
  symbol?: string;
  timeframe: ChartTimeframe | string;
  height?: number;
  liveQuote?: LiveFxQuote | null;
}) {
  const { hostRef, status, message, meta, liveKind, liveUpdated, followLive, goToLive, visibleBarCount, generation, staleDropped } = useFxNativeLiveChart({
    symbol,
    timeframe,
    height,
    liveQuote,
    pricePrecision: 3,
    minMove: 0.001,
    loadError: "Не удалось загрузить бары DXY",
    emptyError: "Нет баров для отображения",
    useApiErrorMessage: true,
  });

  return (
    <div
      className="w-full"
      data-testid="dxy-native-chart"
      data-symbol={symbol}
      data-engine="lightweight-charts"
      data-status={status}
      data-last-close={formatFxQuote(meta.lastClose, 3) ?? ""}
      data-live-follow={followLive ? "yes" : "no"}
      data-visible-range-bars={String(visibleBarCount)}
      data-chart-generation={String(generation)}
      data-stale-live-dropped={String(staleDropped)}
    >
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
        <FxLiveStatusCaption
          testIdPrefix="dxy"
          liveKind={liveKind}
          liveUpdated={liveUpdated}
          followLive={followLive}
          onGoToLive={goToLive}
        />
        <span data-testid="dxy-chart-bars">{message}</span>
        {meta.source ? <span>{meta.source}</span> : null}
        {formatFxQuote(liveQuote?.mid, 3) ? (
          <span data-testid="dxy-live-quote">
            Live: {formatFxQuote(liveQuote?.mid, 3)}
            {liveQuote?.source ? ` · ${String(liveQuote.source)}` : ""}
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
