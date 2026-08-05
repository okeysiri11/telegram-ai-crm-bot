/**
 * Sprint 27.3 — Recent Activity journal (local, persisted).
 */

import { ACTIVITY_JOURNAL_KEY } from "./types";

export type ActivityKind =
  | "navigate"
  | "search"
  | "create"
  | "ai"
  | "error"
  | "login"
  | "system"
  | "notification";

export type ActivityEntry = {
  id: string;
  kind: ActivityKind;
  title: string;
  detail: string;
  at: string;
};

const MAX = 80;

function read(): ActivityEntry[] {
  try {
    const raw = localStorage.getItem(ACTIVITY_JOURNAL_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ActivityEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(items: ActivityEntry[]) {
  try {
    localStorage.setItem(ACTIVITY_JOURNAL_KEY, JSON.stringify(items.slice(0, MAX)));
  } catch {
    /* ignore */
  }
}

export function logActivity(input: Omit<ActivityEntry, "id" | "at"> & { at?: string }) {
  const entry: ActivityEntry = {
    id: `act_${Math.random().toString(36).slice(2, 10)}`,
    at: input.at || new Date().toISOString(),
    kind: input.kind,
    title: input.title,
    detail: input.detail,
  };
  const next = [entry, ...read()].slice(0, MAX);
  write(next);
  return entry;
}

export function listActivity(limit = 40): ActivityEntry[] {
  return read().slice(0, limit);
}

export function clearActivity() {
  write([]);
}
