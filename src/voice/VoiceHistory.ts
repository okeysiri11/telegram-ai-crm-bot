import type { VoiceHistoryEntry, VoiceIntent, VoiceCommandStatus } from "./types.js";

/**
 * Persistent in-memory voice command history for audit and Control Center.
 */
export class VoiceHistory {
  private readonly entries: VoiceHistoryEntry[] = [];
  private readonly max: number;

  constructor(max = 2_000) {
    this.max = max;
  }

  push(
    entry: Omit<VoiceHistoryEntry, "id" | "at"> & { id?: string; at?: string },
  ): VoiceHistoryEntry {
    const full: VoiceHistoryEntry = {
      id:
        entry.id ??
        `vh_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`,
      at: entry.at ?? new Date().toISOString(),
      sessionId: entry.sessionId,
      text: entry.text,
      intent: entry.intent,
      confidence: entry.confidence,
      status: entry.status,
      provider: entry.provider,
      ...(entry.responseText !== undefined
        ? { responseText: entry.responseText }
        : {}),
      ...(entry.chatTaskId !== undefined ? { chatTaskId: entry.chatTaskId } : {}),
      ...(entry.durationMs !== undefined ? { durationMs: entry.durationMs } : {}),
    };
    this.entries.push(full);
    if (this.entries.length > this.max) this.entries.shift();
    return full;
  }

  list(limit = 100): VoiceHistoryEntry[] {
    return [...this.entries].reverse().slice(0, limit);
  }

  listBySession(sessionId: string, limit = 100): VoiceHistoryEntry[] {
    return this.list(limit).filter((e) => e.sessionId === sessionId);
  }

  clear(): void {
    this.entries.length = 0;
  }
}

export type { VoiceIntent, VoiceCommandStatus };

export function createVoiceHistory(max?: number): VoiceHistory {
  return new VoiceHistory(max);
}
