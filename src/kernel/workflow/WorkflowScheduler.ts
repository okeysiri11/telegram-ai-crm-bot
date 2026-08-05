import type { IWorkflowScheduler } from "./interfaces.js";

/**
 * Schedules delayed retries, delays, and resume-after-interruption jobs.
 */
export class WorkflowScheduler implements IWorkflowScheduler {
  private readonly timers = new Map<string, ReturnType<typeof setTimeout>>();

  schedule(
    jobId: string,
    delayMs: number,
    fn: () => void | Promise<void>,
  ): void {
    this.cancel(jobId);
    const timer = setTimeout(() => {
      this.timers.delete(jobId);
      void Promise.resolve(fn()).catch(() => undefined);
    }, Math.max(0, delayMs));
    this.timers.set(jobId, timer);
  }

  cancel(jobId: string): boolean {
    const t = this.timers.get(jobId);
    if (!t) return false;
    clearTimeout(t);
    this.timers.delete(jobId);
    return true;
  }

  clear(): void {
    for (const t of this.timers.values()) clearTimeout(t);
    this.timers.clear();
  }

  pendingCount(): number {
    return this.timers.size;
  }
}
