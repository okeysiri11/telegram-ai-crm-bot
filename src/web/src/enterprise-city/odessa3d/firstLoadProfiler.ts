/**
 * First-load profiler — DEV diagnostics only. Not used on the hot render path.
 */

import type { HeavyClass } from "./assetLifecycle";

export type AssetLoadTiming = {
  id: string;
  url: string;
  sizeMb: number;
  fetchMs: number;
  parseMs: number;
  prepMs: number;
  attachMs: number;
  triangleCount: number;
  objectCount: number;
  heavyClass: HeavyClass;
  longTask: boolean;
};

export type FirstLoadKpis = {
  timeToManifest: number | null;
  timeToFirstParse: number | null;
  timeToFirstGeometry: number | null;
  timeToFirstRender: number | null;
  timeToInteractive: number | null;
  timeTo50PercentActive: number | null;
  timeToReady: number | null;
  totalParseMs: number;
  averageParseMs: number;
  longTaskCount: number;
  longTasks50: number;
  longTasks100: number;
  longTasks250: number;
  longTasks500: number;
  worst10: AssetLoadTiming[];
};

const LONG_TASK_MS = 50;

export class FirstLoadProfiler {
  readonly startedAt: number;
  private manifestAt: number | null = null;
  private firstParseAt: number | null = null;
  private firstGeometryAt: number | null = null;
  private firstRenderAt: number | null = null;
  private interactiveAt: number | null = null;
  private halfAt: number | null = null;
  private readyAt: number | null = null;
  private timings = new Map<string, AssetLoadTiming>();

  constructor(now = performance.now()) {
    this.startedAt = now;
  }

  markManifest(now = performance.now()) {
    if (this.manifestAt == null) this.manifestAt = now;
  }

  recordParse(row: Omit<AssetLoadTiming, "prepMs" | "attachMs" | "longTask">, now = performance.now()) {
    if (this.firstParseAt == null) this.firstParseAt = now;
    this.timings.set(row.id, {
      ...row,
      prepMs: 0,
      attachMs: 0,
      longTask: row.parseMs >= LONG_TASK_MS,
    });
  }

  recordPrep(id: string, prepMs: number) {
    const cur = this.timings.get(id);
    if (cur) cur.prepMs = prepMs;
  }

  recordAttach(id: string, attachMs: number, now = performance.now()) {
    const cur = this.timings.get(id);
    if (cur) cur.attachMs = attachMs;
    if (this.firstGeometryAt == null) this.firstGeometryAt = now;
    if (this.interactiveAt == null) this.interactiveAt = now;
  }

  markFirstRender(now = performance.now()) {
    if (this.firstRenderAt == null) this.firstRenderAt = now;
  }

  markHalf(now = performance.now()) {
    if (this.halfAt == null) this.halfAt = now;
  }

  markReady(now = performance.now()) {
    if (this.readyAt == null) this.readyAt = now;
  }

  snapshot(): FirstLoadKpis {
    const rows = [...this.timings.values()];
    const totalParseMs = rows.reduce((s, r) => s + r.parseMs, 0);
    const worst10 = [...rows].sort((a, b) => b.parseMs - a.parseMs).slice(0, 10);
    const longTasks50 = rows.filter((r) => r.parseMs >= 50).length;
    const longTasks100 = rows.filter((r) => r.parseMs >= 100).length;
    const longTasks250 = rows.filter((r) => r.parseMs >= 250).length;
    const longTasks500 = rows.filter((r) => r.parseMs >= 500).length;
    return {
      timeToManifest: this.manifestAt != null ? this.manifestAt - this.startedAt : null,
      timeToFirstParse: this.firstParseAt != null ? this.firstParseAt - this.startedAt : null,
      timeToFirstGeometry: this.firstGeometryAt != null ? this.firstGeometryAt - this.startedAt : null,
      timeToFirstRender: this.firstRenderAt != null ? this.firstRenderAt - this.startedAt : null,
      timeToInteractive: this.interactiveAt != null ? this.interactiveAt - this.startedAt : null,
      timeTo50PercentActive: this.halfAt != null ? this.halfAt - this.startedAt : null,
      timeToReady: this.readyAt != null ? this.readyAt - this.startedAt : null,
      totalParseMs: +totalParseMs.toFixed(1),
      averageParseMs: rows.length ? +(totalParseMs / rows.length).toFixed(1) : 0,
      longTaskCount: longTasks50,
      longTasks50,
      longTasks100,
      longTasks250,
      longTasks500,
      worst10,
    };
  }

  list(): AssetLoadTiming[] {
    return [...this.timings.values()];
  }
}
