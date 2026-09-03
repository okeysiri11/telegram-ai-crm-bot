/**
 * Native EUR/USD candlesticks via Lightweight Charts.
 * Data: backend /fx-intel/candles (Yahoo EURUSD=X) + live quote overlay. TradingView is not used.
 */
import { useState } from "react";
import { Button } from "@/ui";
import type { ChartTimeframe } from "./chartProvider";
import { formatFxQuote } from "./fxQuoteDisplay";
import type { LiveFxQuote } from "./fxNativeChartCore";
import { FxLiveStatusCaption, useFxNativeLiveChart } from "./useFxNativeLiveChart";

export function EurUsdNativeChart({
  symbol = "EUR/USD",
  timeframe,
  height = 360,
  liveQuote,
}: {
  symbol?: string;
  timeframe: ChartTimeframe | string;
  height?: number;
  liveQuote?: LiveFxQuote | null;
}) {
  const [reload, setReload] = useState(0);
  const { hostRef, status, message, meta, liveKind, liveUpdated, followLive, goToLive, visibleBarCount, generation, staleDropped, sourceNote, displayMode } = useFxNativeLiveChart({
    symbol,
    timeframe,
    height,
    liveQuote,
    pricePrecision: 5,
    minMove: 0.00001,
    loadError: "Не удалось загрузить график EURUSD",
    emptyError: "Не удалось загрузить график EURUSD",
    reload,
  });

  return (
    <div
      className="w-full"
      data-testid="eurusd-native-chart"
      data-symbol={symbol}
      data-engine="lightweight-charts"
      data-status={status}
      data-bar-count={String(meta.barCount)}
      data-last-close={formatFxQuote(meta.lastClose, 5) ?? ""}
      data-live-follow={followLive ? "yes" : "no"}
      data-visible-range-bars={String(visibleBarCount)}
      data-chart-generation={String(generation)}
      data-stale-live-dropped={String(staleDropped)}
      data-source-status={String(meta.sourceStatus || "")}
      data-source-resolution={String(meta.sourceResolution || "")}
      data-base-resolution={String(meta.baseResolution || "")}
      data-displayed-timeframe={String(meta.displayedTimeframe || timeframe)}
      data-aggregated={meta.aggregated ? "yes" : "no"}
      data-provider={String(meta.provider || "")}
      data-data-quality={String(meta.dataQuality || "")}
      data-display-mode={String(meta.displayMode || displayMode || "CANDLES")}
    >
      <div
        ref={hostRef}
        className="w-full overflow-hidden rounded-md border border-[var(--eds-border)] bg-white"
        style={{ height }}
        data-testid="eurusd-chart-canvas"
      />
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 eds-type-caption text-[var(--eds-text-muted)]">
        <span data-testid="eurusd-chart-status">
          {status === "loading"
            ? "Обновление источника…"
            : status === "ready"
              ? "ADOS · Lightweight Charts"
              : status === "unavailable"
                ? "UNAVAILABLE_AT_SOURCE_RESOLUTION"
                : "Ошибка"}
        </span>
        <FxLiveStatusCaption
          testIdPrefix="eurusd"
          liveKind={liveKind}
          liveUpdated={liveUpdated}
          followLive={followLive}
          onGoToLive={goToLive}
          provider={meta.provider || meta.source}
          sourceResolution={meta.sourceResolution}
          barCount={meta.barCount}
          sourceNote={sourceNote}
          baseResolution={meta.baseResolution}
          displayedTimeframe={meta.displayedTimeframe}
          aggregation={meta.aggregation}
          historyKind={meta.historyKind}
          liveQuoteProvider={meta.liveQuoteProvider}
          quality={meta.dataQuality}
          displayMode={meta.displayMode || displayMode}
          degradedReason={meta.degradedReason}
        />
        <span data-testid="eurusd-chart-bars">{message}</span>
        {meta.source ? <span>{meta.source}</span> : null}
        {formatFxQuote(liveQuote?.mid, 5) ? (
          <span data-testid="eurusd-live-quote">
            Live: {formatFxQuote(liveQuote?.mid, 5)}
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
        EUR/USD: история — реальный 1m OHLC (Dukascopy / keyed provider) или линия при DEGRADED Yahoo. Live quote отдельно. TradingView не используется.
      </p>
    </div>
  );
}
