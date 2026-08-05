import type { McpEvent, McpEventType, McpLogEntry } from "./types.js";

export type McpEventListener = (event: McpEvent) => void;

export class MCPEvents {
  private readonly listeners = new Set<McpEventListener>();
  private readonly logs: McpLogEntry[] = [];
  private readonly maxLogs: number;

  constructor(maxLogs = 2_000) {
    this.maxLogs = maxLogs;
  }

  on(listener: McpEventListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  emit(type: McpEventType, payload: unknown): McpEvent {
    const event: McpEvent = {
      type,
      at: new Date().toISOString(),
      payload,
    };
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch {
        /* ignore */
      }
    }
    return event;
  }

  log(
    kind: McpLogEntry["kind"],
    message: string,
    meta?: Readonly<Record<string, unknown>>,
  ): McpLogEntry {
    const entry: McpLogEntry = {
      id: `mcp_log_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`,
      at: new Date().toISOString(),
      kind,
      message,
      ...(meta !== undefined ? { meta } : {}),
    };
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) this.logs.shift();
    return entry;
  }

  listLogs(limit = 100): McpLogEntry[] {
    return [...this.logs].reverse().slice(0, limit);
  }

  clearLogs(): void {
    this.logs.length = 0;
  }
}

export function createMCPEvents(): MCPEvents {
  return new MCPEvents();
}
