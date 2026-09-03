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
export type FxChartTimestamp = UTCTimestamp;

export type NativeCandleBar = {
  t: string;
  o: number;
  h: number;
  l: number;
  c: number;
  v?: number | null;
};

export type SafeCandleUpdateResult = "appended" | "updated" | "dropped_stale" | "dropped_invalid" | "dropped_error";

/** Diagnostic counters — never used to invent prices. */
export let STALE_LIVE_UPDATES_DROPPED = 0;
export let FX_INVALID_TIMESTAMPS_DROPPED = 0;
export let FX_HISTORY_DUPLICATES_DROPPED = 0;
export let STALE_TICKS_APPLIED = 0;
export let SERIES_GENERATION_LEAKS = 0;
export let GIANT_CANDLE_ERRORS = 0;

export function resetFxChartDiagnostics(): void {
  STALE_LIVE_UPDATES_DROPPED = 0;
  FX_INVALID_TIMESTAMPS_DROPPED = 0;
  FX_HISTORY_DUPLICATES_DROPPED = 0;
  STALE_TICKS_APPLIED = 0;
  SERIES_GENERATION_LEAKS = 0;
  GIANT_CANDLE_ERRORS = 0;
}

export function noteStaleTickApplied(): void {
  STALE_TICKS_APPLIED += 1;
  SERIES_GENERATION_LEAKS += 1;
}

/**
 * Canonical Lightweight Charts time: Unix seconds (UTCTimestamp).
 * Rejects NaN/null/undefined. Converts ISO strings and BusinessDay objects
 * so a series never mixes numeric and object times.
 */
export function normalizeChartTime(value: unknown): FxChartTimestamp | null {
  if (value == null) return null;
  if (typeof value === "boolean") return null;
  if (typeof value === "number") {
    if (!Number.isFinite(value) || value <= 0) return null;
    const unix = value > 1e12 ? Math.floor(value / 1000) : Math.floor(value);
    return unix > 0 ? (unix as FxChartTimestamp) : null;
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return null;
    const asNum = Number(trimmed);
    if (Number.isFinite(asNum) && asNum > 0) return normalizeChartTime(asNum);
    const ms = Date.parse(trimmed);
    if (!Number.isFinite(ms) || ms <= 0) return null;
    return Math.floor(ms / 1000) as FxChartTimestamp;
  }
  if (typeof value === "object") {
    const rec = value as { timestamp?: unknown; year?: unknown; month?: unknown; day?: unknown };
    if (rec.timestamp != null) return normalizeChartTime(rec.timestamp);
    const year = Number(rec.year);
    const month = Number(rec.month);
    const day = Number(rec.day);
    if (Number.isFinite(year) && Number.isFinite(month) && Number.isFinite(day) && year > 1970 && month >= 1 && month <= 12) {
      const ms = Date.UTC(year, month - 1, day);
      if (!Number.isFinite(ms) || ms <= 0) return null;
      return Math.floor(ms / 1000) as FxChartTimestamp;
    }
  }
  return null;
}

export function normalizeHistoryCandles(candles: FxCandle[], symbol?: string): FxCandle[] {
  const mapped: FxCandle[] = [];
  for (const candle of candles) {
    const time = normalizeChartTime(candle.time);
    const open = Number(candle.open);
    const high = Number(candle.high);
    const low = Number(candle.low);
    const close = Number(candle.close);
    if (time == null || !fxOhlcValid(open, high, low, close, symbol)) {
      FX_INVALID_TIMESTAMPS_DROPPED += 1;
      continue;
    }
    mapped.push({ time, open, high, low, close });
  }
  mapped.sort((a, b) => Number(a.time) - Number(b.time));
  const out: FxCandle[] = [];
  for (const candle of mapped) {
    const prev = out.at(-1);
    if (prev && Number(prev.time) === Number(candle.time)) {
      out[out.length - 1] = candle;
      FX_HISTORY_DUPLICATES_DROPPED += 1;
      continue;
    }
    if (prev && Number(prev.time) >= Number(candle.time)) {
      FX_INVALID_TIMESTAMPS_DROPPED += 1;
      continue;
    }
    out.push(candle);
  }
  return out;
}

export function barsToCandles(bars: NativeCandleBar[], symbol?: string): CandlestickData[] {
  const raw: FxCandle[] = [];
  for (const b of bars) {
    const open = Number(b.o);
    const high = Number(b.h);
    const low = Number(b.l);
    const close = Number(b.c);
    const time = normalizeChartTime(b.t);
    if (time == null || !fxOhlcValid(open, high, low, close, symbol)) {
      FX_INVALID_TIMESTAMPS_DROPPED += 1;
      continue;
    }
    raw.push({ time, open, high, low, close });
  }
  return normalizeHistoryCandles(raw, symbol);
}

export type FxLinePoint = { time: FxChartTimestamp; value: number };

export function barsToLinePoints(bars: NativeCandleBar[], symbol?: string): FxLinePoint[] {
  const candles = barsToCandles(bars, symbol);
  return candles.map((c) => ({ time: c.time as FxChartTimestamp, value: Number(c.close) }));
}

export function lastSeriesTimestampOf(candles: { time: unknown }[]): number {
  const last = candles.at(-1);
  if (!last) return 0;
  return Number(last.time) || 0;
}

export function safeUpdateCandlestick(
  series: { update: (bar: FxCandle) => void } | null | undefined,
  bar: FxCandle | null | undefined,
  lastSeriesTimestamp: number,
): { result: SafeCandleUpdateResult; lastSeriesTimestamp: number; bar?: FxCandle } {
  if (!series || !bar) return { result: "dropped_invalid", lastSeriesTimestamp };
  const time = normalizeChartTime(bar.time);
  if (time == null) {
    FX_INVALID_TIMESTAMPS_DROPPED += 1;
    return { result: "dropped_invalid", lastSeriesTimestamp };
  }
  const open = Number(bar.open);
  const high = Number(bar.high);
  const low = Number(bar.low);
  const close = Number(bar.close);
  if (![open, high, low, close].every(Number.isFinite)) {
    FX_INVALID_TIMESTAMPS_DROPPED += 1;
    return { result: "dropped_invalid", lastSeriesTimestamp };
  }
  if (Math.min(open, high, low, close) <= 0 || high < low || high / low > 20) {
    FX_INVALID_TIMESTAMPS_DROPPED += 1;
    return { result: "dropped_invalid", lastSeriesTimestamp };
  }
  const newTime = Number(time);
  const lastTime = Number(lastSeriesTimestamp) || 0;
  if (lastTime > 0 && newTime < lastTime) {
    STALE_LIVE_UPDATES_DROPPED += 1;
    console.warn("[fx-chart] dropped stale live bar", { lastTime, newTime });
    return { result: "dropped_stale", lastSeriesTimestamp };
  }
  const normalized: FxCandle = { time, open, high, low, close };
  try {
    series.update(normalized);
  } catch (err) {
    STALE_LIVE_UPDATES_DROPPED += 1;
    console.warn("[fx-chart] series.update rejected", err);
    return { result: "dropped_error", lastSeriesTimestamp };
  }
  return {
    result: lastTime > 0 && newTime === lastTime ? "updated" : "appended",
    lastSeriesTimestamp: newTime,
    bar: normalized,
  };
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

/** Reject unit/format corruption only (EURUSD 11610, DXY 0 / 99230). Never cap real moves. */
export function fxPriceSane(symbol: string | undefined, price: number, ref?: number | null): boolean {
  if (!Number.isFinite(price) || price <= 0) return false;
  const named = String(symbol || "");
  const dxy = /dxy/i.test(named);
  const eurusd = /eur/i.test(named);
  if (dxy) {
    if (price < 20 || price > 200) return false;
  } else if (eurusd) {
    if (price < 0.2 || price > 5) return false;
  } else {
    const inEur = price >= 0.2 && price <= 5;
    const inDxy = price >= 20 && price <= 200;
    if (!inEur && !inDxy) return false;
  }
  if (ref != null && Number.isFinite(ref) && ref > 0) {
    const ratio = price / ref;
    if (ratio > 50 || ratio < 1 / 50) return false;
  }
  return true;
}

export function fxOhlcValid(open: number, high: number, low: number, close: number, symbol?: string): boolean {
  if (![open, high, low, close].every(Number.isFinite)) return false;
  if (Math.min(open, high, low, close) <= 0) return false;
  if (high < low) return false;
  if (high < Math.max(open, close) || low > Math.min(open, close)) return false;
  if (high / low > 20) return false;
  return [open, high, low, close].every((p) => fxPriceSane(symbol, p));
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
  symbol?: string,
): FxCandle | null {
  if (!Number.isFinite(quote) || quote <= 0) return null;
  if (!fxPriceSane(symbol, quote, last?.close)) {
    console.warn("[fx-chart] rejected corrupt quote", { symbol, quote, ref: last?.close });
    return null;
  }
  const ts = Math.floor(Number(quoteUnix));
  if (!Number.isFinite(ts) || ts <= 0) return null;
  const bucket = candleBucketUnix(timeframe, ts);
  if (!bucket) return null;
  const bucketTime = normalizeChartTime(bucket);
  if (bucketTime == null) return null;
  if (!last) {
    return { time: bucketTime, open: quote, high: quote, low: quote, close: quote };
  }
  const lastTime = normalizeChartTime(last.time);
  if (lastTime == null) {
    return { time: bucketTime, open: quote, high: quote, low: quote, close: quote };
  }
  const lastBucket = candleBucketUnix(timeframe, Number(lastTime));
  if (bucket < lastBucket) return null;
  if (bucket === lastBucket) {
    return {
      time: lastTime,
      open: last.open,
      high: Math.max(last.high, quote),
      low: Math.min(last.low, quote),
      close: quote,
    };
  }
  return {
    time: bucketTime,
    open: quote,
    high: quote,
    low: quote,
    close: quote,
  };
}

/** Quote may only mutate the active last bucket. Historical bars stay byte-stable. */
export function applyLiveQuoteToHistory(
  history: FxCandle[],
  quote: number,
  quoteUnix: number,
  timeframe: string,
  symbol?: string,
): { history: FxCandle[]; mutatedHistorical: boolean } {
  const snapshot = history.map((b) => ({ ...b }));
  const last = snapshot.at(-1) ?? null;
  const next = applyQuoteToActiveCandle(last, quote, quoteUnix, timeframe, symbol);
  if (!next) return { history: snapshot, mutatedHistorical: false };
  const body = Math.abs(next.high - next.low);
  if (next.close > 0 && body / next.close > 0.05) {
    GIANT_CANDLE_ERRORS += 1;
  }
  if (!last) return { history: [next], mutatedHistorical: false };
  const lastTime = Number(last.time);
  const nextTime = Number(next.time);
  if (nextTime < lastTime) return { history: snapshot, mutatedHistorical: false };
  if (nextTime === lastTime) {
    const historical = snapshot.slice(0, -1);
    const mutatedHistorical = historical.some((b, i) => {
      const orig = history[i];
      return !orig || orig.open !== b.open || orig.high !== b.high || orig.low !== b.low || orig.close !== b.close || Number(orig.time) !== Number(b.time);
    });
    return { history: [...historical, next], mutatedHistorical };
  }
  const mutatedHistorical = snapshot.some((b, i) => {
    const orig = history[i];
    return !orig || orig.open !== b.open || orig.high !== b.high || orig.low !== b.low || orig.close !== b.close || Number(orig.time) !== Number(b.time);
  });
  return { history: [...snapshot, next], mutatedHistorical };
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
export const FX_BAR_SPACING = 6;
export const FX_MIN_BAR_SPACING = 3;

export function fxVisibleBarCount(timeframe: string): number {
  const tf = normalizeCandlesTimeframe(timeframe);
  if (tf === "1m" || tf === "5m" || tf === "15m") return 100;
  if (tf === "1H") return 90;
  if (tf === "4H") return 80;
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
