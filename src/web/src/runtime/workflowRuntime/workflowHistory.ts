/**
 * Workflow history — Sprint 28.8.
 */

import type { WorkflowHistoryEntry, WorkflowStatus } from "./workflowTypes";

export const WORKFLOW_HISTORY_KEY = "ews_workflow_history_v1";

function read(): WorkflowHistoryEntry[] {
  try {
    const raw = localStorage.getItem(WORKFLOW_HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as WorkflowHistoryEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(items: WorkflowHistoryEntry[]) {
  try {
    localStorage.setItem(WORKFLOW_HISTORY_KEY, JSON.stringify(items.slice(0, 100)));
  } catch {
    /* ignore */
  }
}

export const workflowHistory = {
  list(limit = 40): WorkflowHistoryEntry[] {
    if (typeof window === "undefined") return [];
    return read().slice(0, limit);
  },

  push(entry: Omit<WorkflowHistoryEntry, "id"> & { id?: string }): WorkflowHistoryEntry {
    const full: WorkflowHistoryEntry = {
      id: entry.id || `wh_${Math.random().toString(36).slice(2, 10)}`,
      sessionId: entry.sessionId,
      definitionId: entry.definitionId,
      name: entry.name,
      status: entry.status,
      startedAt: entry.startedAt,
      completedAt: entry.completedAt,
      durationMs: entry.durationMs,
      error: entry.error,
    };
    write([full, ...read()].slice(0, 100));
    return full;
  },

  clear() {
    write([]);
  },

  byStatus(status: WorkflowStatus) {
    return this.list(80).filter((e) => e.status === status);
  },
};
