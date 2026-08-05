/**
 * Automation execution queue — Sprint 28.9.
 */

import type { AutomationJob, AutomationQueueStatus, AutomationTimelineEvent } from "./automationTypes";

const jobs = new Map<string, AutomationJob>();
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

function timeline(type: string, message: string): AutomationTimelineEvent {
  return {
    id: `tl_${Math.random().toString(36).slice(2, 8)}`,
    at: new Date().toISOString(),
    type,
    message,
  };
}

export const automationQueue = {
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  list(status?: AutomationQueueStatus): AutomationJob[] {
    const all = [...jobs.values()].sort((a, b) => {
      if (b.priority !== a.priority) return b.priority - a.priority;
      return b.createdAt.localeCompare(a.createdAt);
    });
    return status ? all.filter((j) => j.status === status) : all;
  },

  get(id: string) {
    return jobs.get(id);
  },

  enqueue(job: Omit<AutomationJob, "timeline"> & { timeline?: AutomationTimelineEvent[] }): AutomationJob {
    const full: AutomationJob = {
      ...job,
      timeline: [...(job.timeline || []), timeline("enqueued", `Queued (${job.triggerKind})`)],
    };
    jobs.set(full.id, full);
    emit();
    return full;
  },

  update(id: string, patch: Partial<AutomationJob>, event?: { type: string; message: string }) {
    const cur = jobs.get(id);
    if (!cur) return null;
    const next: AutomationJob = {
      ...cur,
      ...patch,
      timeline: event
        ? [timeline(event.type, event.message), ...cur.timeline].slice(0, 80)
        : cur.timeline,
    };
    jobs.set(id, next);
    emit();
    return next;
  },

  remove(id: string) {
    const ok = jobs.delete(id);
    if (ok) emit();
    return ok;
  },

  counts() {
    const c: Record<AutomationQueueStatus, number> = {
      pending: 0,
      running: 0,
      waiting: 0,
      completed: 0,
      failed: 0,
      cancelled: 0,
      retry: 0,
    };
    for (const j of jobs.values()) c[j.status] += 1;
    return c;
  },

  clearTerminal() {
    for (const j of [...jobs.values()]) {
      if (j.status === "completed" || j.status === "failed" || j.status === "cancelled") {
        jobs.delete(j.id);
      }
    }
    emit();
  },

  clear() {
    jobs.clear();
    emit();
  },
};
