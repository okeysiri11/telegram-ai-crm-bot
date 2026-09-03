/**
 * Shared FX native-chart helpers (Lightweight Charts + /fx-intel/candles).
 */
import { type CandlestickData, type UTCTimestamp } from "lightweight-charts";
import { cryptoFxIntelGet } from "../business-ops/opsApi";

export const LIVE_QUOTE_STALE_MS = 30_000;
export const FX_HISTORY_REFRESH_MS = 60_000;
export const FX_QUOTE_POLL_MS = 5_000;

export type LiveFxQuote = {
  mid?: unknown;
  source?: string;
  fetched_at?: string;
  status?: string;
  market_time?: unknown;
};

export type FxCandle = CandlestickData;

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
  const ordered = [...bars].sort((a, b) => Date.parse(String(a.t)) - Date.parse(String(b.t)));
  const out: CandlestickData[] = [];
  let prev = 0;
  for (const b of ordered) {
    const o = Number(b.o);
    const h = Number(b.h);
    const l = Number(b.l);
    const c = Number(b.c);
    if (![o, h, l, c].every(Number.isFinite)) continue;
    let t = toUtcTs(b.t);
    if (t <= prev) t = (prev + 1) as UTCTimestamp;
    prev = t;
    out.push({ time: t, open: o, high: h, low: l, close: c });
  }
  return out;
}

export function normalizeCandlesTimeframe(tf: string): string {
  const u = tf.trim();
  const map: Record<string, string> = {
    "1m": "1m",
    "1M": "1m",
    "5m": "5m",
    "5M": "5m",
    "15m": "15m",
    "15M": "15m",
    "1h": "1H",
    "1H": "1H",
    "4h": "4H",
    "4H": "4H",
    "1d": "1D",
    "1D": "1D",
    "1w": "1W",
    "1W": "1W",
  };
  return map[u] || "1H";
}

export async function fetchFxCandles(symbol: string, timeframe: string, signal?: AbortSignal) {
  const tf = normalizeCandlesTimeframe(timeframe);
  const res = await cryptoFxIntelGet(
    `/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(tf)}`,
    signal,
  );
  return { ok: res.ok, json: (res.json || {}) as Record<string, unknown>, cancelled: Boolean(res.cancelled) };
}

export function fxHistoryRefreshMs(timeframe: string): number {
  const tf = normalizeCandlesTimeframe(timeframe);
  return tf === "1m" || tf === "5m" || tf === "15m" ? FX_HISTORY_REFRESH_MS : 0;
}

export function parseQuoteMid(value: unknown): number | null {
  if (value == null || value === "") return null;
  const n = typeof value === "number" ? value : Number(String(value).trim().replace(",", "."));
  if (!Number.isFinite(n) || n <= 0) return null;
  return n;
}

export function quoteTimeUnix(quote: LiveFxQuote | null | undefined, nowMs = Date.now()): number {
  const fetched = Date.parse(String(quote?.fetched_at || ""));
  if (Number.isFinite(fetched) && fetched > 0) return Math.floor(fetched / 1000);
  const mt = Number(quote?.market_time);
  if (Number.isFinite(mt) && mt > 1e9) return Math.floor(mt);
  return Math.floor(nowMs / 1000);
}

export function candleBucketUnix(timeframe: string, atUnix: number): number {
  const t = Math.floor(Number(atUnix));
  if (!Number.isFinite(t) || t <= 0) return 0;
  const tf = normalizeCandlesTimeframe(timeframe);
  if (tf === "1m") return Math.floor(t / 60) * 60;
  if (tf === "5m") return Math.floor(t / 300) * 300;
  if (tf === "15m") return Math.floor(t / 900) * 900;
  if (tf === "1H") return Math.floor(t / 3600) * 3600;
  if (tf === "4H") return Math.floor(t / 14_400) * 14_400;
  if (tf === "1D") {
    const d = new Date(t * 1000);
    return Math.floor(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) / 1000);
  }
  const d = new Date(t * 1000);
  const day = d.getUTCDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  return Math.floor(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() + mondayOffset) / 1000);
}

export function applyQuoteToActiveCandle(
  last: FxCandle | null,
  quote: number,
  quoteUnix: number,
  timeframe: string,
): FxCandle | null {
  if (!Number.isFinite(quote) || quote <= 0) return null;
  const ts = Math.floor(Number(quoteUnix));
  if (!Number.isFinite(ts) || ts <= 0) return null;
  const bucket = candleBucketUnix(timeframe, ts) as UTCTimestamp;
  if (!bucket) return null;
  if (!last) {
    return { time: bucket, open: quote, high: quote, low: quote, close: quote };
  }
  const lastTime = Number(last.time);
  const lastBucket = candleBucketUnix(timeframe, lastTime);
  if (bucket < lastBucket) return null;
  if (bucket === lastBucket) {
    return {
      time: last.time,
      open: last.open,
      high: Math.max(last.high, quote),
      low: Math.min(last.low, quote),
      close: quote,
    };
  }
  const open = last.close;
  return {
    time: bucket,
    open,
    high: Math.max(open, quote),
    low: Math.min(open, quote),
    close: quote,
  };
}

export function formatLiveUpdated(fetchedAt: string | undefined, locale?: string): string | null {
  const ms = Date.parse(String(fetchedAt || ""));
  if (!Number.isFinite(ms)) return null;
  try {
    return new Date(ms).toLocaleTimeString(locale, { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    const d = new Date(ms);
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    const ss = String(d.getSeconds()).padStart(2, "0");
    return `${hh}:${mm}:${ss}`;
  }
}

export function liveQuoteIsStale(lastQuoteMs: number | null, nowMs = Date.now()): boolean {
  if (lastQuoteMs == null || !Number.isFinite(lastQuoteMs)) return true;
  return nowMs - lastQuoteMs > LIVE_QUOTE_STALE_MS;
}

export const FX_PRICE_SCALE_MARGIN_TOP = 0.12;
export const FX_PRICE_SCALE_MARGIN_BOTTOM = 0.12;
export const FX_LIVE_FOLLOW_RIGHT_PAD = 4;

export function fxVisibleBarCount(timeframe: string): number {
  const tf = normalizeCandlesTimeframe(timeframe);
  if (tf === "1m" || tf === "5m" || tf === "15m") return 120;
  if (tf === "1H" || tf === "4H") return 100;
  if (tf === "1D") return 90;
  if (tf === "1W") return 70;
  return 100;
}

export function fxInitialLogicalRange(
  barCount: number,
  visibleCount: number,
  rightPad = FX_LIVE_FOLLOW_RIGHT_PAD,
): { from: number; to: number } {
  const last = Math.max(0, barCount - 1);
  const window = Math.max(1, Math.min(visibleCount, Math.max(barCount, 1)));
  const from = Math.max(0, last - window + 1);
  return { from, to: last + rightPad };
}

export function userLeftLiveFollow(
  range: { from: number; to: number } | null | undefined,
  lastIndex: number,
): boolean {
  if (!range || !Number.isFinite(Number(range.to))) return false;
  return Number(range.to) < lastIndex - 1;
}
