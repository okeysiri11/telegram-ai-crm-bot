/**
 * Main-thread GLB parse scheduler.
 * One synchronous GLTF.parse at a time; yield after each (double-rAF after heavy).
 * Does not claim worker parse. A started parse cannot be cancelled.
 */

import type { BootState, HeavyClass } from "../assetLifecycle";
import type { RuntimePerfMode } from "../runtimePerfState";
import { yieldAfterParse } from "./browserYield";
import {
  PARSE_CONCURRENCY,
  applyParseStarvation,
  canStartParse,
  isHeavyParseClass,
  parseBandRank,
  type ParseBand,
} from "./parsePolicy";
import type { ParseDiagnostics } from "./parseDiagnostics";

export type ParseJob = {
  id: string;
  url: string;
  buffer: ArrayBuffer;
  sizeMb: number;
  heavyClass: HeavyClass;
  score: number;
  queuedAt: number;
  prefetch?: boolean;
  seaProtected?: boolean;
  nearTarget?: boolean;
  inFrustum?: boolean;
  screenImportant?: boolean;
  parseBand: ParseBand;
  triangleCount?: number;
  objectCount?: number;
};

export type ParseResult = {
  root: import("three").Object3D;
  objectCount?: number;
};

export type ParseSchedulerRuntime = {
  mode: RuntimePerfMode;
  fps: number;
  bootState: BootState;
};

export type ParseFn = (job: ParseJob) => Promise<ParseResult> | ParseResult;

export type ParseSchedulerOptions = {
  parseFn: ParseFn;
  diagnostics: ParseDiagnostics;
  yieldFn?: (heavy: boolean) => Promise<void>;
  now?: () => number;
};

export class ParseScheduler {
  private jobs = new Map<string, ParseJob>();
  private parsingId: string | null = null;
  private pumping = false;
  private aborted = false;
  private lastParseMs = 0;
  private runtime: ParseSchedulerRuntime = { mode: "IDLE", fps: 60, bootState: "BOOTSTRAP" };
  private parseFn: ParseFn;
  private diagnostics: ParseDiagnostics;
  private yieldFn: (heavy: boolean) => Promise<void>;
  private now: () => number;
  private onParsed: ((id: string, result: ParseResult, parseMs: number) => void) | null = null;
  private onFailed: ((id: string, error: Error) => void) | null = null;

  constructor(opts: ParseSchedulerOptions) {
    this.parseFn = opts.parseFn;
    this.diagnostics = opts.diagnostics;
    this.yieldFn = opts.yieldFn ?? yieldAfterParse;
    this.now = opts.now ?? (() => performance.now());
  }

  setHandlers(handlers: {
    onParsed: (id: string, result: ParseResult, parseMs: number) => void;
    onFailed: (id: string, error: Error) => void;
  }) {
    this.onParsed = handlers.onParsed;
    this.onFailed = handlers.onFailed;
  }

  setRuntime(runtime: Partial<ParseSchedulerRuntime>) {
    this.runtime = { ...this.runtime, ...runtime };
  }

  enqueue(job: ParseJob) {
    if (this.aborted || this.jobs.has(job.id) || this.parsingId === job.id) return;
    this.jobs.set(job.id, job);
  }

  updatePriority(
    id: string,
    patch: Partial<Pick<ParseJob, "score" | "parseBand" | "nearTarget" | "inFrustum" | "seaProtected" | "screenImportant" | "prefetch">>,
  ) {
    const job = this.jobs.get(id);
    if (!job) return;
    Object.assign(job, patch);
  }

  waitingCount(): number {
    return this.jobs.size;
  }

  waitingMb(): number {
    let mb = 0;
    for (const j of this.jobs.values()) mb += j.sizeMb;
    return mb;
  }

  isParsing(): boolean {
    return this.parsingId != null;
  }

  currentParseId(): string | null {
    return this.parsingId;
  }

  lastParseDuration(): number {
    return this.lastParseMs;
  }

  hasId(id: string): boolean {
    return this.jobs.has(id) || this.parsingId === id;
  }

  drop(id: string): ArrayBuffer | null {
    if (this.parsingId === id) return null;
    const job = this.jobs.get(id);
    if (!job) return null;
    this.jobs.delete(id);
    return job.buffer;
  }

  waitingIds(): string[] {
    return [...this.jobs.keys()];
  }

  /** True if any waiting job is more important than `band` (non-prefetch). */
  hasHigherPriorityThan(band: ParseBand, prefetch = false): boolean {
    const rank = parseBandRank(band);
    for (const job of this.jobs.values()) {
      if (job.prefetch && !prefetch) continue;
      const effective = applyParseStarvation(job.parseBand, this.now() - job.queuedAt);
      if (parseBandRank(effective) < rank) return true;
    }
    return false;
  }

  dispose() {
    this.aborted = true;
    this.jobs.clear();
    this.parsingId = null;
    this.pumping = false;
  }

  async pump(): Promise<void> {
    if (this.aborted || this.pumping) return;
    this.pumping = true;
    try {
      while (!this.aborted) {
        const next = this.pickNext();
        if (!next) break;
        this.jobs.delete(next.id);
        const heavy = isHeavyParseClass(next.heavyClass);
        await this.runOne(next);
        if (this.aborted) break;
        await this.yieldFn(heavy);
      }
    } finally {
      this.pumping = false;
    }
  }

  private pickNext(): ParseJob | null {
    if (this.jobs.size === 0 || this.parsingId) return null;
    const rows = [...this.jobs.values()];
    rows.sort((a, b) => this.rank(a) - this.rank(b));
    for (const job of rows) {
      const band = applyParseStarvation(job.parseBand, this.now() - job.queuedAt);
      if (
        canStartParse({
          heavyClass: job.heavyClass,
          mode: this.runtime.mode,
          fps: this.runtime.fps,
          lastParseMs: this.lastParseMs,
          bootState: this.runtime.bootState,
          nearTarget: !!job.nearTarget,
          seaProtected: !!job.seaProtected,
          screenImportant: job.screenImportant,
          parseBand: band,
          prefetch: job.prefetch,
          higherPriorityWaiting: this.hasHigherPriorityThan(band, !!job.prefetch),
          currentlyParsing: this.parsingId != null,
        })
      ) {
        return job;
      }
    }
    return null;
  }

  private rank(job: ParseJob): number {
    const waitMs = Math.max(0, this.now() - job.queuedAt);
    const band = applyParseStarvation(job.parseBand, waitMs);
    const prefetchPenalty = job.prefetch ? 10_000 : 0;
    return parseBandRank(band) * 10_000 + job.score + prefetchPenalty;
  }

  private async runOne(job: ParseJob): Promise<void> {
    this.parsingId = job.id;
    this.diagnostics.beginParse(job.id, job.sizeMb, this.now());
    const t0 = this.now();
    try {
      const result = await this.parseFn(job);
      const parseMs = +(this.now() - t0).toFixed(1);
      this.lastParseMs = parseMs;
      this.diagnostics.endParse(
        {
          id: job.id,
          url: job.url,
          sizeMb: job.sizeMb,
          fetchMs: 0,
          parseMs,
          triangleCount: job.triangleCount ?? 0,
          objectCount: result.objectCount ?? job.objectCount ?? 0,
          heavyClass: job.heavyClass,
        },
        this.now(),
      );
      this.onParsed?.(job.id, result, parseMs);
    } catch (err) {
      const parseMs = +(this.now() - t0).toFixed(1);
      this.lastParseMs = parseMs;
      const error = err instanceof Error ? err : new Error(String(err));
      this.diagnostics.recordFailure(job.id, job.url, "parsing", error.message, job.sizeMb);
      this.onFailed?.(job.id, error);
    } finally {
      this.parsingId = null;
    }
  }
}

export const PARSE_CONCURRENCY_LIMIT = PARSE_CONCURRENCY;
