/**
 * Normalized HUD progress — Odessa 3D first paint must never read missing fields.
 * `total` is 0 until the manifest registers assets, then the real loader count (45).
 */

import type { BootState, LoadingProgress } from "./types";

export type HudProgress = {
  total: number;
  loaded: number;
  failed: number;
  queued: number;
  loading: number;
  percent: number;
  downloaded: number;
  parsed: number;
  active: number;
  loadedMb: number;
  totalMb: number;
  mb: number;
  fps: number;
  boot: BootState;
  ready: boolean;
  currentAssetId: string | null;
  firstError: string | null;
  loadingAssetId: string | null;
  loadDiagnostics: NonNullable<LoadingProgress["loadDiagnostics"]>;
};

const EMPTY: HudProgress = {
  total: 0,
  loaded: 0,
  failed: 0,
  queued: 0,
  loading: 0,
  percent: 0,
  downloaded: 0,
  parsed: 0,
  active: 0,
  loadedMb: 0,
  totalMb: 0,
  mb: 0,
  fps: 0,
  boot: "BOOTSTRAP",
  ready: false,
  currentAssetId: null,
  firstError: null,
  loadingAssetId: null,
  loadDiagnostics: [],
};

function num(v: unknown, fallback = 0): number {
  const n = typeof v === "number" && Number.isFinite(v) ? v : Number(v);
  return Number.isFinite(n) ? n : fallback;
}

export function normalizeHudProgress(
  raw?: Partial<LoadingProgress> | null,
  perf?: { fps?: number } | null,
): HudProgress {
  if (!raw) {
    return { ...EMPTY, fps: num(perf?.fps, 0) };
  }
  const boot =
    raw.bootState === "INTERACTIVE" ||
    raw.bootState === "FILLING" ||
    raw.bootState === "READY" ||
    raw.bootState === "BOOTSTRAP"
      ? raw.bootState
      : "BOOTSTRAP";
  const loadedMb = num(raw.loadedMb, 0);
  return {
    total: num(raw.total, 0),
    loaded: num(raw.loaded, 0),
    failed: num(raw.failed, 0),
    queued: num(raw.queued, 0),
    loading: num(raw.loading, 0),
    percent: Math.min(100, Math.max(0, num(raw.percent, 0))),
    downloaded: num(raw.downloadedCount, 0),
    parsed: num(raw.parsedCount, 0),
    active: num(raw.activeCount, 0),
    loadedMb,
    totalMb: num(raw.totalMb, 0),
    mb: loadedMb,
    fps: num(perf?.fps, 0),
    boot,
    ready: boot === "READY",
    currentAssetId: raw.currentAssetId ?? raw.loadingAssetId ?? null,
    firstError: raw.firstError ?? null,
    loadingAssetId: raw.loadingAssetId ?? null,
    loadDiagnostics: Array.isArray(raw.loadDiagnostics) ? raw.loadDiagnostics : [],
  };
}

export const EMPTY_HUD_PROGRESS: HudProgress = EMPTY;
