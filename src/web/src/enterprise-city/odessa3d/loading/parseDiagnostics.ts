/**
 * Bounded GLB pipeline diagnostics + performance marks.
 * Marks are capped so a 45-asset city does not retain them forever.
 */

import type { HeavyClass } from "../assetLifecycle";

export const LONG_TASK_50 = 50;
export const LONG_TASK_100 = 100;
export const LONG_TASK_250 = 250;
export const LONG_TASK_500 = 500;

const MARK_PREFIX = "odessa25:";
const MAX_MARKS = 40;

export type AssetPipelineTiming = {
  id: string;
  url: string;
  sizeMb: number;
  fetchMs: number;
  parseMs: number;
  prepMs: number;
  attachMs: number;
  totalBlockingMs: number;
  triangleCount: number;
  objectCount: number;
  heavyClass: HeavyClass;
  error?: string;
  stage?: string;
};

export type LongTaskBuckets = {
  ge50: number;
  ge100: number;
  ge250: number;
  ge500: number;
};

export type PipelineQueueSnapshot = {
  fetching: number;
  waitingParse: number;
  parsing: number;
  parsed: number;
  waitingActivation: number;
  active: number;
  hidden: number;
  failed: number;
  fetchingMb: number;
  waitingParseMb: number;
  parsingMb: number;
  parsedMb: number;
  waitingActivationMb: number;
  activeMb: number;
  hiddenMb: number;
  fetchQueue: number;
  parseQueue: number;
  activationQueue: number;
  fetchConcurrent: number;
  parseConcurrent: number;
  backpressure: boolean;
};

export type GlbPipelineDiagnostics = PipelineQueueSnapshot & {
  currentParseId: string | null;
  currentParseSizeMb: number;
  currentParseElapsedMs: number;
  lastParseMs: number;
  averageParseMs: number;
  worstParseMs: number;
  longTasks50: number;
  longTasks100: number;
  longTasks250: number;
  longTasks500: number;
  worstOffenders: Array<{ id: string; parseMs: number; sizeMb: number; triangleCount: number }>;
};

function supportMarks(): boolean {
  return typeof performance !== "undefined" && typeof performance.mark === "function";
}

export class ParseDiagnostics {
  private timings = new Map<string, AssetPipelineTiming>();
  private markSeq: string[] = [];
  private lastParseMs = 0;
  private parseStartedAt = 0;
  private currentParseId: string | null = null;
  private currentParseSizeMb = 0;

  recordFetch(id: string, patch: Partial<AssetPipelineTiming> & { url?: string; sizeMb?: number }) {
    const cur = this.timings.get(id) ?? emptyTiming(id, patch.url || "", patch.sizeMb ?? 0);
    this.timings.set(id, { ...cur, ...patch, id });
  }

  beginParse(id: string, sizeMb: number, now = performance.now()) {
    this.currentParseId = id;
    this.currentParseSizeMb = sizeMb;
    this.parseStartedAt = now;
    this.mark(`parse:start:${id}`);
  }

  endParse(
    row: Omit<AssetPipelineTiming, "prepMs" | "attachMs" | "totalBlockingMs">,
    now = performance.now(),
  ) {
    this.lastParseMs = row.parseMs;
    this.currentParseId = null;
    this.currentParseSizeMb = 0;
    this.parseStartedAt = 0;
    const cur = this.timings.get(row.id) ?? emptyTiming(row.id, row.url, row.sizeMb);
    const blocking = row.parseMs + (cur.prepMs || 0) + (cur.attachMs || 0);
    this.timings.set(row.id, {
      ...cur,
      ...row,
      totalBlockingMs: +blocking.toFixed(1),
    });
    this.mark(`parse:end:${row.id}`);
    this.measure(`parse:${row.id}`, `parse:start:${row.id}`, `parse:end:${row.id}`);
    void now;
  }

  recordPrep(id: string, prepMs: number) {
    const cur = this.timings.get(id);
    if (!cur) return;
    cur.prepMs = prepMs;
    cur.totalBlockingMs = +(cur.parseMs + prepMs + (cur.attachMs || 0)).toFixed(1);
  }

  recordAttach(id: string, attachMs: number) {
    const cur = this.timings.get(id);
    if (!cur) return;
    cur.attachMs = attachMs;
    cur.totalBlockingMs = +(cur.parseMs + (cur.prepMs || 0) + attachMs).toFixed(1);
  }

  recordFailure(id: string, url: string, stage: string, error: string, sizeMb = 0) {
    const cur = this.timings.get(id) ?? emptyTiming(id, url, sizeMb);
    this.timings.set(id, { ...cur, error, stage, url, sizeMb });
    this.currentParseId = null;
    this.parseStartedAt = 0;
  }

  buckets(): LongTaskBuckets {
    const rows = [...this.timings.values()];
    return {
      ge50: rows.filter((r) => r.parseMs >= LONG_TASK_50).length,
      ge100: rows.filter((r) => r.parseMs >= LONG_TASK_100).length,
      ge250: rows.filter((r) => r.parseMs >= LONG_TASK_250).length,
      ge500: rows.filter((r) => r.parseMs >= LONG_TASK_500).length,
    };
  }

  snapshot(queue: PipelineQueueSnapshot, now = performance.now()): GlbPipelineDiagnostics {
    const rows = [...this.timings.values()].filter((r) => r.parseMs > 0);
    const total = rows.reduce((s, r) => s + r.parseMs, 0);
    const worst = [...rows].sort((a, b) => b.parseMs - a.parseMs);
    const buckets = this.buckets();
    const elapsed = this.currentParseId ? Math.max(0, now - this.parseStartedAt) : 0;
    return {
      ...queue,
      currentParseId: this.currentParseId,
      currentParseSizeMb: this.currentParseSizeMb,
      currentParseElapsedMs: +elapsed.toFixed(1),
      lastParseMs: this.lastParseMs,
      averageParseMs: rows.length ? +(total / rows.length).toFixed(1) : 0,
      worstParseMs: worst[0]?.parseMs ?? 0,
      longTasks50: buckets.ge50,
      longTasks100: buckets.ge100,
      longTasks250: buckets.ge250,
      longTasks500: buckets.ge500,
      worstOffenders: worst.slice(0, 10).map((r) => ({
        id: r.id,
        parseMs: r.parseMs,
        sizeMb: r.sizeMb,
        triangleCount: r.triangleCount,
      })),
    };
  }

  list(): AssetPipelineTiming[] {
    return [...this.timings.values()];
  }

  dispose() {
    this.timings.clear();
    this.currentParseId = null;
    if (supportMarks()) {
      try {
        performance.clearMarks(MARK_PREFIX);
        performance.clearMeasures(MARK_PREFIX);
      } catch {
        for (const name of this.markSeq) {
          try {
            performance.clearMarks(name);
            performance.clearMeasures(name);
          } catch {
            /* ignore */
          }
        }
      }
    }
    this.markSeq = [];
  }

  private mark(suffix: string) {
    if (!supportMarks()) return;
    const name = `${MARK_PREFIX}${suffix}`;
    try {
      performance.mark(name);
      this.markSeq.push(name);
      while (this.markSeq.length > MAX_MARKS) {
        const old = this.markSeq.shift();
        if (old) performance.clearMarks(old);
      }
    } catch {
      /* ignore */
    }
  }

  private measure(nameSuffix: string, startSuffix: string, endSuffix: string) {
    if (!supportMarks() || typeof performance.measure !== "function") return;
    try {
      performance.measure(`${MARK_PREFIX}${nameSuffix}`, `${MARK_PREFIX}${startSuffix}`, `${MARK_PREFIX}${endSuffix}`);
    } catch {
      /* missing marks */
    }
  }
}

function emptyTiming(id: string, url: string, sizeMb: number): AssetPipelineTiming {
  return {
    id,
    url,
    sizeMb,
    fetchMs: 0,
    parseMs: 0,
    prepMs: 0,
    attachMs: 0,
    totalBlockingMs: 0,
    triangleCount: 0,
    objectCount: 0,
    heavyClass: "LIGHT",
  };
}
