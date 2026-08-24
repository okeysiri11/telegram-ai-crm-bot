/**
 * Optional PerformanceObserver("longtask") — diagnostics/dev only.
 * Feature-detected. Never used for parse scheduling correctness.
 * Safari typically does not implement longtask; observer then stays idle.
 */

export type ObservedLongTask = {
  duration: number;
  startTime: number;
};

const MAX_TASKS = 32;

export function supportsLongTaskObserver(): boolean {
  if (typeof PerformanceObserver !== "function") return false;
  const supported = PerformanceObserver.supportedEntryTypes;
  if (!supported) return false;
  return [...supported].includes("longtask");
}

export class DevLongTaskObserver {
  private observer: PerformanceObserver | null = null;
  private tasks: ObservedLongTask[] = [];

  start() {
    if (this.observer || !supportsLongTaskObserver()) return;
    try {
      this.observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.tasks.push({ duration: entry.duration, startTime: entry.startTime });
          if (this.tasks.length > MAX_TASKS) this.tasks.shift();
        }
      });
      this.observer.observe({ type: "longtask", buffered: true });
    } catch {
      this.observer = null;
    }
  }

  stop() {
    this.observer?.disconnect();
    this.observer = null;
  }

  snapshot(): ObservedLongTask[] {
    return [...this.tasks];
  }

  dispose() {
    this.stop();
    this.tasks = [];
  }
}
