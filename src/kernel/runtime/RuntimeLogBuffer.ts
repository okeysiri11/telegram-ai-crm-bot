import type { LogEntry } from "./types.js";

/**
 * In-memory ring buffer for runtime logs (live, not mocked).
 */
export class RuntimeLogBuffer {
  private readonly entries: LogEntry[] = [];
  private seq = 0;
  private readonly capacity: number;

  constructor(capacity = 2_000) {
    this.capacity = capacity;
  }

  push(
    level: LogEntry["level"],
    message: string,
    source?: string,
  ): LogEntry {
    this.seq += 1;
    const entry: LogEntry = {
      id: `log_${this.seq}`,
      at: new Date().toISOString(),
      level,
      message,
      ...(source !== undefined ? { source } : {}),
    };
    this.entries.push(entry);
    if (this.entries.length > this.capacity) {
      this.entries.shift();
    }
    return entry;
  }

  list(filter?: {
    level?: LogEntry["level"];
    q?: string;
    limit?: number;
  }): readonly LogEntry[] {
    let rows = [...this.entries].reverse();
    if (filter?.level) {
      rows = rows.filter((e) => e.level === filter.level);
    }
    if (filter?.q) {
      const q = filter.q.toLowerCase();
      rows = rows.filter((e) => e.message.toLowerCase().includes(q));
    }
    if (filter?.limit !== undefined) {
      rows = rows.slice(0, filter.limit);
    }
    return Object.freeze(rows);
  }

  clear(): void {
    this.entries.length = 0;
  }
}
