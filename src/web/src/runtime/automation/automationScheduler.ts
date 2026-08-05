/**
 * Automation scheduler — Sprint 28.9.
 * Interval-based schedules (no external cron dependency).
 */

type ScheduleHandler = () => void;

type ScheduleEntry = {
  automationId: string;
  intervalMs: number;
  timer: ReturnType<typeof setInterval> | null;
};

const schedules = new Map<string, ScheduleEntry>();
let tickHandler: ((automationId: string) => void) | null = null;

export const automationScheduler = {
  setHandler(handler: (automationId: string) => void) {
    tickHandler = handler;
  },

  register(automationId: string, intervalMs: number) {
    this.unregister(automationId);
    if (intervalMs <= 0) return false;
    const entry: ScheduleEntry = {
      automationId,
      intervalMs: Math.max(1000, intervalMs),
      timer: null,
    };
    entry.timer = setInterval(() => {
      tickHandler?.(automationId);
    }, entry.intervalMs);
    schedules.set(automationId, entry);
    return true;
  },

  unregister(automationId: string) {
    const cur = schedules.get(automationId);
    if (cur?.timer) clearInterval(cur.timer);
    schedules.delete(automationId);
  },

  list() {
    return [...schedules.values()].map((s) => ({
      automationId: s.automationId,
      intervalMs: s.intervalMs,
    }));
  },

  clear() {
    for (const id of [...schedules.keys()]) this.unregister(id);
  },

  /** Test helper — fire once without waiting */
  fire(automationId: string) {
    tickHandler?.(automationId);
  },
};

export type { ScheduleHandler };
