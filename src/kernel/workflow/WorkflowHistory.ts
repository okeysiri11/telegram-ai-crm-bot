import type { WorkflowHistoryEntry } from "./types.js";

let histSeq = 0;

/**
 * In-memory workflow history / persistence log (plugin can swap store later).
 */
export class WorkflowHistory {
  private readonly byInstance = new Map<string, WorkflowHistoryEntry[]>();
  private readonly all: WorkflowHistoryEntry[] = [];

  append(
    entry: Omit<WorkflowHistoryEntry, "id" | "at"> & {
      id?: string;
      at?: string;
    },
  ): WorkflowHistoryEntry {
    histSeq += 1;
    const full: WorkflowHistoryEntry = {
      id: entry.id ?? `wh_${histSeq}`,
      instanceId: entry.instanceId,
      at: entry.at ?? new Date().toISOString(),
      type: entry.type,
      ...(entry.stepId !== undefined ? { stepId: entry.stepId } : {}),
      ...(entry.message !== undefined ? { message: entry.message } : {}),
      ...(entry.data !== undefined ? { data: entry.data } : {}),
    };
    const list = this.byInstance.get(entry.instanceId) ?? [];
    list.push(full);
    this.byInstance.set(entry.instanceId, list);
    this.all.push(full);
    return full;
  }

  list(instanceId: string): readonly WorkflowHistoryEntry[] {
    return Object.freeze([...(this.byInstance.get(instanceId) ?? [])]);
  }

  /** Persistence snapshot for resume-after-interruption. */
  persistAll(): readonly WorkflowHistoryEntry[] {
    return Object.freeze([...this.all]);
  }

  clear(instanceId?: string): void {
    if (instanceId) {
      this.byInstance.delete(instanceId);
      for (let i = this.all.length - 1; i >= 0; i -= 1) {
        if (this.all[i]?.instanceId === instanceId) this.all.splice(i, 1);
      }
      return;
    }
    this.byInstance.clear();
    this.all.length = 0;
  }
}
