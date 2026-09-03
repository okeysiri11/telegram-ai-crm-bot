/**
 * Shared FX native-chart helpers (Lightweight Charts + /fx-intel/candles).
 */
import { type CandlestickData, type UTCTimestamp } from "lightweight-charts";
import { cryptoFxIntelGet } from "../business-ops/opsApi";

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

export async function fetchFxCandles(symbol: string, timeframe: string) {
  const tf = normalizeCandlesTimeframe(timeframe);
  const res = await cryptoFxIntelGet(`/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(tf)}`);
  return { ok: res.ok, json: (res.json || {}) as Record<string, unknown> };
}
