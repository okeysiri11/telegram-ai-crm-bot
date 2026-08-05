/**
 * Command history · favorites · pinned — Sprint 28.6.
 * Bridges palette commandRecent / commandFavorites for UI compatibility.
 */

import { commandFavorites, commandRecent } from "@/command-center-runtime/commandFavorites";
import type { CommandHistoryEntry } from "./commandTypes";

export const COMMAND_HISTORY_KEY = "ews_cmd_history_v1";
export const COMMAND_PINNED_KEY = "ews_cmd_pinned_v1";

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeJson(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore */
  }
}

export const commandHistory = {
  list(limit = 40): CommandHistoryEntry[] {
    if (typeof window === "undefined") return [];
    const all = readJson<CommandHistoryEntry[]>(COMMAND_HISTORY_KEY, []);
    return all.slice(0, limit);
  },

  push(entry: Omit<CommandHistoryEntry, "id" | "at"> & { at?: string }): CommandHistoryEntry {
    const full: CommandHistoryEntry = {
      id: `ch_${Math.random().toString(36).slice(2, 10)}`,
      at: entry.at || new Date().toISOString(),
      commandId: entry.commandId,
      action: entry.action,
      label: entry.label,
      ok: entry.ok,
      route: entry.route,
      error: entry.error,
    };
    const next = [full, ...this.list(80)].slice(0, 80);
    writeJson(COMMAND_HISTORY_KEY, next);
    // Keep palette Recent section in sync
    try {
      commandRecent.push(entry.commandId);
    } catch {
      /* ignore */
    }
    return full;
  },

  recentCommandIds(limit = 20): string[] {
    const seen = new Set<string>();
    const out: string[] = [];
    for (const e of this.list(40)) {
      if (seen.has(e.commandId)) continue;
      seen.add(e.commandId);
      out.push(e.commandId);
      if (out.length >= limit) break;
    }
    return out;
  },

  lastExecuted(): CommandHistoryEntry | null {
    return this.list(1)[0] || null;
  },

  clear() {
    writeJson(COMMAND_HISTORY_KEY, []);
  },

  favorites(): string[] {
    return commandFavorites.list();
  },

  toggleFavorite(commandId: string): string[] {
    return commandFavorites.toggle(commandId);
  },

  isFavorite(commandId: string): boolean {
    return commandFavorites.isFavorite(commandId);
  },

  pinned(): string[] {
    if (typeof window === "undefined") return [];
    return readJson<string[]>(COMMAND_PINNED_KEY, []);
  },

  togglePin(commandId: string): string[] {
    const cur = this.pinned();
    const next = cur.includes(commandId)
      ? cur.filter((id) => id !== commandId)
      : [commandId, ...cur].slice(0, 16);
    writeJson(COMMAND_PINNED_KEY, next);
    return next;
  },

  isPinned(commandId: string): boolean {
    return this.pinned().includes(commandId);
  },
};
