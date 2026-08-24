/**
 * TradingView public embed — honest DXY fallback when widget unavailable.
 * Never substitute another instrument under the DXY label.
 */
import { useEffect, useId, useRef, useState } from "react";

export type TradingViewEmbedProps = {
  symbol: string;
  interval?: string;
  height?: number;
  /** Backend quote mid for honest fallback when TV widget fails (esp. DXY). */
  fallbackQuote?: { mid?: unknown; source?: string; fetched_at?: string; status?: string } | null;
};

const TV_MAP: Record<string, string> = {
  "EUR/USD": "FX:EURUSD",
  EURUSD: "FX:EURUSD",
  DXY: "TVC:DXY",
  USDX: "TVC:DXY",
};

const TF_MAP: Record<string, string> = {
  "15m": "15",
  "15M": "15",
  "1h": "60",
  "1H": "60",
  "4h": "240",
  "4H": "240",
  "1d": "D",
  "1D": "D",
};

declare global {
  interface Window {
    TradingView?: {
      widget: new (opts: Record<string, unknown>) => unknown;
    };
  }
}

function loadTvScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.TradingView) {
      resolve();
      return;
    }
    const existing = document.querySelector('script[data-ados-tv="1"]') as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("TradingView script failed")));
      return;
    }
    const s = document.createElement("script");
    s.src = "https://s3.tradingview.com/tv.js";
    s.async = true;
    s.dataset.adosTv = "1";
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("TradingView script failed"));
    document.head.appendChild(s);
  });
}

export function tvSymbolFor(instrument: string): string {
  return TV_MAP[instrument] || TV_MAP[instrument.toUpperCase()] || instrument;
}

export function TradingViewEmbed({ symbol, interval = "1H", height = 420, fallbackQuote }: TradingViewEmbedProps) {
  const reactId = useId().replace(/:/g, "");
  const containerId = `ados_tv_${reactId}`;
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const isDxy = symbol.toUpperCase() === "DXY" || symbol.toUpperCase() === "USDX";

  useEffect(() => {
    let cancelled = false;
    const tvSymbol = tvSymbolFor(symbol);
    // Critical: never remap DXY to a different instrument
    if (isDxy && tvSymbol !== "TVC:DXY") {
      setUnavailable(true);
      return;
    }
    const tvInterval = TF_MAP[interval] || "60";
    setUnavailable(false);

    void (async () => {
      try {
        await loadTvScript();
        if (cancelled || !window.TradingView || !hostRef.current) return;
        hostRef.current.innerHTML = "";
        const mount = document.createElement("div");
        mount.id = containerId;
        mount.style.height = `${height}px`;
        hostRef.current.appendChild(mount);
        // eslint-disable-next-line no-new
        new window.TradingView.widget({
          autosize: true,
          symbol: tvSymbol,
          interval: tvInterval,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Etc/UTC",
          theme: "light",
          style: "1",
          locale: "ru",
          toolbar_bg: "#f1f3f6",
          enable_publishing: false,
          allow_symbol_change: false,
          hide_side_toolbar: false,
          container_id: containerId,
          height,
          width: "100%",
        });
        // Soft detect: if TV blocks DXY, show honest fallback after delay without swapping symbol
        if (isDxy) {
          window.setTimeout(() => {
            if (cancelled) return;
            const iframe = hostRef.current?.querySelector("iframe");
            if (!iframe) setUnavailable(true);
          }, 4000);
        }
      } catch {
        if (!cancelled) setUnavailable(true);
      }
    })();

    return () => {
      cancelled = true;
      if (hostRef.current) hostRef.current.innerHTML = "";
    };
  }, [symbol, interval, height, containerId, isDxy]);

  if (unavailable) {
    return (
      <div
        className="w-full overflow-hidden rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface)] p-4"
        data-testid="tradingview-fallback"
        data-symbol={tvSymbolFor(symbol)}
      >
        <p className="eds-type-body font-medium">{symbol}</p>
        <p className="eds-type-small text-[var(--eds-text-muted)]">
          {isDxy
            ? "Виджет TradingView (TVC:DXY) недоступен или ограничен. Котировка DXY берётся с бэкенда (Yahoo). График другого инструмента не подставляется."
            : "График TradingView временно недоступен. Проверьте сеть."}
        </p>
        {fallbackQuote?.mid != null ? (
          <p className="mt-2 eds-type-small">
            Котировка: {String(fallbackQuote.mid)}
            {fallbackQuote.source ? ` · ${String(fallbackQuote.source)}` : ""}
            {fallbackQuote.fetched_at ? ` · ${String(fallbackQuote.fetched_at)}` : ""}
          </p>
        ) : (
          <p className="mt-2 eds-type-small text-[var(--eds-warning,#b45309)]">Нет актуальной котировки бэкенда</p>
        )}
      </div>
    );
  }

  return (
    <div
      className="tradingview-widget-container w-full overflow-hidden rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface)]"
      data-testid="tradingview-embed"
      data-symbol={tvSymbolFor(symbol)}
    >
      <div ref={hostRef} style={{ height }} />
      <p className="eds-type-caption px-2 py-1 text-[var(--eds-text-muted)]">
        TradingView · {tvSymbolFor(symbol)} · без входа в аккаунт
      </p>
    </div>
  );
}
