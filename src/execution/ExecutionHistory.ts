import type { ExecutionPlanSnapshot, ExecutionReport } from "./types.js";

export interface HistoryEntry {
  readonly id: string;
  readonly at: string;
  readonly planId: string;
  readonly status: string;
  readonly progress: number;
  readonly report?: ExecutionReport;
  readonly snapshot?: ExecutionPlanSnapshot;
}

/**
 * Stores completed/partial plan history for Control Center and API.
 */
export class ExecutionHistory {
  private readonly entries: HistoryEntry[] = [];
  private readonly max: number;

  constructor(max = 500) {
    this.max = max;
  }

  push(
    entry: Omit<HistoryEntry, "id" | "at"> & { id?: string; at?: string },
  ): HistoryEntry {
    const full: HistoryEntry = {
      id:
        entry.id ??
        `eh_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`,
      at: entry.at ?? new Date().toISOString(),
      planId: entry.planId,
      status: entry.status,
      progress: entry.progress,
      ...(entry.report !== undefined ? { report: entry.report } : {}),
      ...(entry.snapshot !== undefined ? { snapshot: entry.snapshot } : {}),
    };
    this.entries.push(full);
    if (this.entries.length > this.max) this.entries.shift();
    return full;
  }

  list(limit = 50): HistoryEntry[] {
    return [...this.entries].reverse().slice(0, limit);
  }

  getByPlanId(planId: string): HistoryEntry | undefined {
    return [...this.entries].reverse().find((e) => e.planId === planId);
  }
}

export function createExecutionHistory(): ExecutionHistory {
  return new ExecutionHistory();
}
