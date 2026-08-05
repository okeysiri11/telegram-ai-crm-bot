/**
 * Automation history — Sprint 28.9.
 */

import { AUTOMATION_HISTORY_KEY, type AutomationHistoryEntry, type AutomationQueueStatus } from "./automationTypes";

function read(): AutomationHistoryEntry[] {
  try {
    const raw = localStorage.getItem(AUTOMATION_HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as AutomationHistoryEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(items: AutomationHistoryEntry[]) {
  try {
    localStorage.setItem(AUTOMATION_HISTORY_KEY, JSON.stringify(items.slice(0, 120)));
  } catch {
    /* ignore */
  }
}

export const automationHistory = {
  list(limit = 40): AutomationHistoryEntry[] {
    if (typeof window === "undefined") return [];
    return read().slice(0, limit);
  },

  push(entry: Omit<AutomationHistoryEntry, "id" | "at"> & { id?: string; at?: string }) {
    const full: AutomationHistoryEntry = {
      id: entry.id || `ah_${Math.random().toString(36).slice(2, 10)}`,
      at: entry.at || new Date().toISOString(),
      jobId: entry.jobId,
      automationId: entry.automationId,
      workflowId: entry.workflowId,
      status: entry.status,
      triggerKind: entry.triggerKind,
      attempt: entry.attempt,
      durationMs: entry.durationMs,
      error: entry.error,
    };
    write([full, ...read()].slice(0, 120));
    return full;
  },

  clear() {
    write([]);
  },

  stats() {
    const all = this.list(120);
    const completed = all.filter((e) => e.status === "completed").length;
    const failed = all.filter((e) => e.status === "failed").length;
    const total = completed + failed;
    const durations = all.map((e) => e.durationMs || 0).filter((n) => n > 0);
    const avg =
      durations.length > 0
        ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length)
        : 0;
    return {
      total: all.length,
      completed,
      failed,
      successRate: total ? completed / total : 1,
      failureRate: total ? failed / total : 0,
      avgDurationMs: avg,
      retries: all.reduce((s, e) => s + Math.max(0, e.attempt - 1), 0),
    };
  },

  byStatus(status: AutomationQueueStatus) {
    return this.list(80).filter((e) => e.status === status);
  },
};
