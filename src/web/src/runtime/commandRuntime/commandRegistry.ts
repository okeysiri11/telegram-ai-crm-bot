/**
 * Command registry — Sprint 28.6.
 */

import type { CommandDefinition } from "./commandTypes";

const byId = new Map<string, CommandDefinition>();
const byAction = new Map<string, CommandDefinition>();
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

export const commandRegistry = {
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },

  register(def: CommandDefinition): CommandDefinition {
    byId.set(def.id, def);
    byAction.set(def.action, def);
    emit();
    return def;
  },

  registerMany(defs: CommandDefinition[]) {
    for (const d of defs) this.register(d);
  },

  unregister(id: string) {
    const def = byId.get(id);
    if (!def) return false;
    byId.delete(id);
    if (byAction.get(def.action)?.id === id) byAction.delete(def.action);
    emit();
    return true;
  },

  get(idOrAction: string): CommandDefinition | undefined {
    return byId.get(idOrAction) || byAction.get(idOrAction);
  },

  list(): CommandDefinition[] {
    return [...byId.values()];
  },

  search(query: string, limit = 24): CommandDefinition[] {
    const q = query.trim().toLowerCase();
    if (!q) return this.list().slice(0, limit);
    return this.list()
      .map((d) => {
        const hay = [d.id, d.action, d.label, ...d.keywords].join(" ").toLowerCase();
        let score = 0;
        if (d.label.toLowerCase().startsWith(q)) score += 8;
        if (hay.includes(q)) score += 4;
        for (const part of q.split(/\s+/)) {
          if (hay.includes(part)) score += 1;
        }
        return { d, score };
      })
      .filter((x) => x.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map((x) => x.d);
  },

  clear() {
    byId.clear();
    byAction.clear();
    emit();
  },
};
