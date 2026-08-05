/**
 * Active workflow sessions store — Sprint 28.8.
 */

import type { WorkflowSession } from "./workflowTypes";
import { WORKFLOW_PERSIST_KEY } from "./workflowTypes";
import { createWorkflowSession, logSession } from "./workflowContext";

export { createWorkflowSession, logSession, createWorkflowContext } from "./workflowContext";

const sessions = new Map<string, WorkflowSession>();
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

export function persistSessions() {
  try {
    const payload = {
      version: 1,
      at: new Date().toISOString(),
      sessions: [...sessions.values()],
    };
    localStorage.setItem(WORKFLOW_PERSIST_KEY, JSON.stringify(payload));
  } catch {
    /* ignore */
  }
}

export function hydrateSessions() {
  try {
    const raw = localStorage.getItem(WORKFLOW_PERSIST_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw) as { sessions?: WorkflowSession[] };
    for (const s of parsed.sessions || []) {
      if (s.status === "running" || s.status === "waiting" || s.status === "paused") {
        // Restore as paused so inspector can resume (avoid auto-fire timers)
        if (s.status === "running") s.status = "paused";
        sessions.set(s.id, s);
      }
    }
    emit();
  } catch {
    /* ignore */
  }
}

export const workflowSessions = {
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  get(id: string) {
    return sessions.get(id);
  },

  list() {
    return [...sessions.values()].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  },

  set(session: WorkflowSession) {
    sessions.set(session.id, session);
    persistSessions();
    emit();
  },

  remove(id: string) {
    sessions.delete(id);
    persistSessions();
    emit();
  },

  byStatus(status: WorkflowSession["status"]) {
    return this.list().filter((s) => s.status === status);
  },

  clearTerminal() {
    for (const s of [...sessions.values()]) {
      if (s.status === "completed" || s.status === "failed" || s.status === "cancelled") {
        sessions.delete(s.id);
      }
    }
    persistSessions();
    emit();
  },
};
