import type { AgentLogEntry } from "./types.js";

/**
 * Per-agent execution history for Control Center Agent Logs.
 */
export class AgentLogBuffer {
  private readonly entries: AgentLogEntry[] = [];
  private readonly max: number;

  constructor(max = 2_000) {
    this.max = max;
  }

  push(
    entry: Omit<AgentLogEntry, "id" | "at"> & { id?: string; at?: string },
  ): AgentLogEntry {
    const full: AgentLogEntry = {
      id: entry.id ?? `alog_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
      at: entry.at ?? new Date().toISOString(),
      agentId: entry.agentId,
      level: entry.level,
      message: entry.message,
      ...(entry.taskId !== undefined ? { taskId: entry.taskId } : {}),
      ...(entry.meta !== undefined ? { meta: entry.meta } : {}),
    };
    this.entries.push(full);
    if (this.entries.length > this.max) this.entries.shift();
    return full;
  }

  list(opts?: {
    agentId?: string;
    level?: AgentLogEntry["level"];
    limit?: number;
  }): AgentLogEntry[] {
    let rows = [...this.entries].reverse();
    if (opts?.agentId) rows = rows.filter((e) => e.agentId === opts.agentId);
    if (opts?.level) rows = rows.filter((e) => e.level === opts.level);
    return rows.slice(0, opts?.limit ?? 200);
  }

  clear(): void {
    this.entries.length = 0;
  }
}
